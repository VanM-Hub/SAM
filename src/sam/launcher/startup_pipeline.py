"""
OP-374 — Startup Pipeline

Pipeline startup resmi SAM:

  Application → Environment → Diagnostics → Configuration
  → Runtime Registry → Guardian Runtime → Host → READY

Semua stage memiliki status.
Pipeline synchronous — tidak ada background worker.
"""

import os
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional
from enum import Enum

from sam.launcher.application import LauncherApplication, LauncherContext, LauncherState
from sam.launcher.runtime_bootstrap import RuntimeBootstrapOrchestrator
from sam.launcher.runtime_registry import RuntimeRegistry, RuntimeType, RuntimeDescriptor
from sam.launcher.host_launcher import HostLauncher, HostLaunchResult
from sam.launcher.host_manager import HostType
from sam.launcher.startup_report import StartupReport, StageResult, StartupIssue, IssueSeverity


class PipelineStage(Enum):
    """Ordered stages in the startup pipeline."""

    APPLICATION = "application"
    ENVIRONMENT = "environment"
    DIAGNOSTICS = "diagnostics"
    CONFIGURATION = "configuration"
    RUNTIME_REGISTRY = "runtime_registry"
    GUARDIAN_RUNTIME = "guardian_runtime"
    HOST = "host"
    READY = "ready"


PIPELINE_ORDER = [
    PipelineStage.APPLICATION,
    PipelineStage.ENVIRONMENT,
    PipelineStage.DIAGNOSTICS,
    PipelineStage.CONFIGURATION,
    PipelineStage.RUNTIME_REGISTRY,
    PipelineStage.GUARDIAN_RUNTIME,
    PipelineStage.HOST,
    PipelineStage.READY,
]


@dataclass(frozen=True)
class PipelineResult:
    """Result of the full startup pipeline."""

    stages: List[StageResult] = field(default_factory=list)
    total_duration_ms: float = 0.0
    success: bool = True
    host_result: Optional[HostLaunchResult] = None
    report: Optional[StartupReport] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "stages": [s.to_dict() for s in self.stages],
            "host_result": self.host_result.to_dict() if self.host_result else None,
        }


class StartupPipeline:
    """Official SAM startup pipeline.

    Orchestrates all stages from Application → READY.
    """

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace or os.getcwd()
        self._orchestrator = RuntimeBootstrapOrchestrator(workspace)
        self._launcher = HostLauncher(workspace)
        self._registry = RuntimeRegistry()

    def run(self) -> PipelineResult:
        """Run the full pipeline. Returns result with all stage outcomes."""
        stages: List[StageResult] = []
        issues: List[StartupIssue] = []
        start = time.perf_counter()

        # ── Stage 1: Application ──
        app = LauncherApplication()
        app_ctx = LauncherContext()
        app_state = LauncherState.INIT
        stages.append(self._make_stage(PipelineStage.APPLICATION, True, 0.0))

        # ── Stage 2: Environment ──
        env_ok = True
        env_start = time.perf_counter()
        try:
            orc_report = self._orchestrator.run(app_ctx)
            env_ok = orc_report.success
        except Exception as exc:
            env_ok = False
            issues.append(StartupIssue(
                stage="environment",
                severity=IssueSeverity.ERROR,
                message=f"Orchestration failed: {exc}",
            ))
        env_dur = (time.perf_counter() - env_start) * 1000
        stages.append(self._make_stage(PipelineStage.ENVIRONMENT, env_ok, env_dur))

        # ── Stage 3: Diagnostics ──
        diag_ok = True
        diag_start = time.perf_counter()
        try:
            if app_ctx.diagnostics_snapshot:
                checks = app_ctx.diagnostics_snapshot.summary
                app_ctx.metadata["diagnostics_passed"] = checks.passed
                app_ctx.metadata["diagnostics_failed"] = checks.failed
            if app_ctx.metadata.get("env_failed", 0) > 0:
                issues.append(StartupIssue(
                    stage="environment",
                    severity=IssueSeverity.WARNING,
                    message=f"Environment checks failed: {app_ctx.metadata['env_failed']} failure(s)",
                ))
        except Exception as exc:
            diag_ok = False
            issues.append(StartupIssue(
                stage="diagnostics",
                severity=IssueSeverity.ERROR,
                message=f"Diagnostics analysis failed: {exc}",
            ))
        diag_dur = (time.perf_counter() - diag_start) * 1000
        stages.append(self._make_stage(PipelineStage.DIAGNOSTICS, diag_ok, diag_dur))

        # ── Stage 4: Configuration ──
        cfg_ok = app_ctx.config is not None
        if app_ctx.metadata.get("config_errors"):
            issues.append(StartupIssue(
                stage="configuration",
                severity=IssueSeverity.WARNING,
                message=f"Configuration errors: {', '.join(app_ctx.metadata['config_errors'][:3])}",
            ))
        stages.append(self._make_stage(PipelineStage.CONFIGURATION, cfg_ok, 0.0))

        # ── Stage 5: Runtime Registry ──
        registry_ok = True
        reg_start = time.perf_counter()
        try:
            registry = app_ctx.metadata.get("__runtime_registry")
            if registry is None:
                from sam.launcher.runtime_registry import RuntimeRegistry
                registry = RuntimeRegistry()
            self._registry = registry
            # Register known runtimes
            for rt, name in [
                (RuntimeType.GUARDIAN, "Guardian Runtime"),
                (RuntimeType.REASONING, "Reasoning Runtime"),
                (RuntimeType.DECISION, "Decision Runtime"),
                (RuntimeType.CONVERSATION, "Conversation Runtime"),
                (RuntimeType.CONSOLE, "Console Host"),
                (RuntimeType.DESKTOP, "Desktop Host"),
                (RuntimeType.HEADLESS, "Headless Mode"),
            ]:
                path = f"sam.{'guardian' if rt == RuntimeType.GUARDIAN else 'operations'}.runtime"
                self._registry.register(RuntimeDescriptor(
                    type=rt, name=name, path=path, available=True,
                ))
        except Exception as exc:
            registry_ok = False
            issues.append(StartupIssue(
                stage="runtime_registry",
                severity=IssueSeverity.ERROR,
                message=f"Registry init failed: {exc}",
            ))
        reg_dur = (time.perf_counter() - reg_start) * 1000
        stages.append(self._make_stage(PipelineStage.RUNTIME_REGISTRY, registry_ok, reg_dur))

        # ── Stage 6: Guardian Runtime ──
        guard_ok = app_ctx.metadata.get("guardian_available", False)
        stages.append(self._make_stage(PipelineStage.GUARDIAN_RUNTIME, guard_ok, 0.0))

        if not guard_ok:
            issues.append(StartupIssue(
                stage="guardian_runtime",
                severity=IssueSeverity.WARNING,
                message="Guardian Runtime module not available",
            ))

        # ── Stage 7: Host ──
        host_result: Optional[HostLaunchResult] = None
        host_ok = False
        host_start = time.perf_counter()

        host_type_str = app_ctx.metadata.get("selected_host", "console")
        # selected_host may arrive as a display name (e.g. "Desktop Host" /
        # "API Server") or a raw key ("desktop" / "api_server"). Normalize to
        # the lowercase underscore key used by host_map so the requested host is
        # selected instead of silently falling back to CONSOLE.
        norm = host_type_str.strip().lower().replace(" ", "_").replace("host", "")
        norm = norm.rstrip("_").lstrip("_")
        aliases = {"desktop": "desktop", "headless_mode": "headless"}
        norm = aliases.get(norm, norm)
        host_map = {
            "console": HostType.CONSOLE,
            "desktop": HostType.DESKTOP,
            "headless": HostType.HEADLESS,
            "api_server": HostType.API_SERVER,
            "testing": HostType.TESTING,
            "diagnostics": HostType.DIAGNOSTICS,
        }
        htype = host_map.get(norm, HostType.CONSOLE)

        try:
            host_result = self._launcher.launch(htype)
            host_ok = host_result.success
            app_ctx.host_type = host_result.host_type
        except Exception as exc:
            issues.append(StartupIssue(
                stage="host",
                severity=IssueSeverity.ERROR,
                message=f"Host launch failed: {exc}",
            ))
        host_dur = (time.perf_counter() - host_start) * 1000
        stages.append(self._make_stage(PipelineStage.HOST, host_ok, host_dur))

        # ── Stage 8: READY ──
        ready_ok = host_ok or (htype in (HostType.TESTING, HostType.DIAGNOSTICS))
        stages.append(self._make_stage(PipelineStage.READY, ready_ok, 0.0))

        if not ready_ok:
            issues.append(StartupIssue(
                stage="ready",
                severity=IssueSeverity.ERROR,
                message="Pipeline did not reach READY state",
            ))

        # ── Build report ──
        total = round((time.perf_counter() - start) * 1000, 1)
        overall = all(s.success for s in stages)

        report = StartupReport(
            stages=stages,
            total_duration_ms=total,
            success=overall,
            issues=issues,
            summary=StartupIssue(
                stage="pipeline",
                severity=IssueSeverity.INFO,
                message=f"Pipeline completed in {total:.0f}ms: "
                        f"{sum(1 for s in stages if s.success)}/{len(stages)} stages OK",
            ),
        )

        return PipelineResult(
            stages=stages,
            total_duration_ms=total,
            success=overall,
            host_result=host_result,
            report=report,
        )

    @staticmethod
    def _make_stage(stage: PipelineStage, success: bool, duration_ms: float) -> StageResult:
        return StageResult(
            stage=stage.value,
            success=success,
            duration_ms=round(duration_ms, 1),
        )
