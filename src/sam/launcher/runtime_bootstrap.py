"""
OP-371 — Runtime Bootstrap Orchestrator

Menghubungkan:
  Application → BootstrapManager → EnvironmentValidator
  → Diagnostics → Guardian Runtime → Host Manager → Host

Hanya orchestration — tidak ada business logic.
"""

import os
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from sam.launcher.application import LauncherApplication, LauncherContext, LauncherState
from sam.launcher.bootstrap import BootstrapManager
from sam.launcher.environment import EnvironmentValidator
from sam.launcher.config_loader import ConfigLoader
from sam.launcher.diagnostics import DiagnosticsEngine
from sam.launcher.host_manager import HostManager
from sam.launcher.safe_mode import SafeModeManager
from sam.launcher.runtime_registry import RuntimeRegistry


@dataclass(frozen=True)
class OrchestratorStep:
    """Single step in the orchestration pipeline."""

    name: str
    success: bool
    duration_ms: float
    detail: str = ""
    error: str = ""


@dataclass(frozen=True)
class OrchestratorReport:
    """Full orchestration report."""

    steps: List[OrchestratorStep] = field(default_factory=list)
    total_duration_ms: float = 0.0
    success: bool = True

    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "total_duration_ms": self.total_duration_ms,
            "steps": [
                {
                    "name": s.name,
                    "success": s.success,
                    "duration_ms": s.duration_ms,
                    "detail": s.detail,
                    "error": s.error,
                }
                for s in self.steps
            ],
        }


class RuntimeBootstrapOrchestrator:
    """Orchestrates the full startup pipeline.

    Wires:
      Application → BootstrapManager
      → EnvironmentValidator
      → Diagnostics
      → Guardian Runtime detection
      → HostManager
      → selected Host
    """

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace or os.getcwd()
        self._steps: List[OrchestratorStep] = []
        self._start_time: float = 0.0

    def run(self, ctx: LauncherContext) -> OrchestratorReport:
        """Run the full orchestration pipeline."""
        self._start_time = time.perf_counter()

        # Stage 1: Application init
        self._step("Application", lambda: self._init_application(ctx))

        # Stage 2: Bootstrap
        self._step("Bootstrap", lambda: self._run_bootstrap(ctx))

        # Stage 3: Environment Validation (skippable)
        if not (ctx.safe_mode and ctx.safe_mode.skip_environment_validation):
            self._step("Environment Validation", lambda: self._validate_environment(ctx))
        else:
            self._add_skipped("Environment Validation")

        # Stage 4: Configuration Loading
        self._step("Configuration Loading", lambda: self._load_configuration(ctx))

        # Stage 5: Diagnostics (skippable)
        if not (ctx.safe_mode and ctx.safe_mode.skip_diagnostics):
            self._step("Diagnostics", lambda: self._run_diagnostics(ctx))
        else:
            self._add_skipped("Diagnostics")

        # Stage 6: Guardian Runtime detection
        self._step("Guardian Runtime", lambda: self._detect_guardian(ctx))

        # Stage 7: Registry initialization
        self._step("Runtime Registry", lambda: self._init_registry(ctx))

        # Stage 8: Host selection
        self._step("Host Selection", lambda: self._select_host(ctx))

        return self._build_report()

    # ── internal pipeline steps ──

    def _init_application(self, ctx: LauncherContext) -> None:
        ctx.state = LauncherState.INIT
        # Application is already initialized; nothing else needed

    def _run_bootstrap(self, ctx: LauncherContext) -> None:
        ctx.state = LauncherState.BOOTSTRAP
        mgr = BootstrapManager()
        report = mgr.run(ctx)
        ctx.metadata["bootstrap_steps"] = len(report.steps)

    def _validate_environment(self, ctx: LauncherContext) -> None:
        ctx.state = LauncherState.VALIDATION
        validator = EnvironmentValidator(self._workspace)
        report = validator.validate()
        ctx.env_report = report
        ctx.metadata["env_passed"] = report.passed
        ctx.metadata["env_failed"] = report.failed

    def _load_configuration(self, ctx: LauncherContext) -> None:
        loader = ConfigLoader(self._workspace)
        config, errors = loader.load()
        ctx.config = config
        ctx.metadata["config_errors"] = errors

    def _run_diagnostics(self, ctx: LauncherContext) -> None:
        engine = DiagnosticsEngine(self._workspace)
        snapshot = engine.snapshot()
        ctx.diagnostics_snapshot = snapshot
        ctx.metadata["diagnostics_checks"] = snapshot.summary.total_checks

    def _detect_guardian(self, ctx: LauncherContext) -> None:
        try:
            import importlib
            mod = importlib.import_module("sam.guardian.engine")
            ctx.metadata["guardian_available"] = True
            ctx.metadata["guardian_version"] = getattr(mod, "__version__", "unknown")
        except ImportError:
            ctx.metadata["guardian_available"] = False

    def _init_registry(self, ctx: LauncherContext) -> None:
        registry = RuntimeRegistry()
        ctx.metadata["registered_runtimes"] = len(registry.list())
        # Store registry for later start by host launcher
        ctx.metadata["__runtime_registry"] = registry

    def _select_host(self, ctx: LauncherContext) -> None:
        from sam.launcher.host_manager import HostType, HostManager
        mgr = HostManager()
        host_type_str = ctx.config.host if ctx.config else "console"

        host_map = {
            "console": HostType.CONSOLE,
            "desktop": HostType.DESKTOP,
            "headless": HostType.HEADLESS,
            "api_server": HostType.API_SERVER,
            "testing": HostType.TESTING,
            "diagnostics": HostType.DIAGNOSTICS,
        }
        htype = host_map.get(host_type_str, HostType.CONSOLE)
        host = mgr.select(htype)
        ctx.host_type = htype.value
        ctx.metadata["selected_host"] = host.display_name if host else "fallback"
        ctx.metadata["host_available"] = host is not None if host else False

    # ── helpers ──

    def _step(self, name: str, fn) -> None:
        start = time.perf_counter()
        try:
            fn()
            dur = (time.perf_counter() - start) * 1000
            self._steps.append(OrchestratorStep(name=name, success=True, duration_ms=round(dur, 1)))
        except Exception as exc:
            dur = (time.perf_counter() - start) * 1000
            self._steps.append(
                OrchestratorStep(name=name, success=False, duration_ms=round(dur, 1), error=str(exc))
            )

    def _add_skipped(self, name: str) -> None:
        self._steps.append(
            OrchestratorStep(name=name, success=True, duration_ms=0.0, detail="skipped (safe mode)")
        )

    def _build_report(self) -> OrchestratorReport:
        total = round((time.perf_counter() - self._start_time) * 1000, 1)
        success = all(s.success for s in self._steps)
        return OrchestratorReport(steps=self._steps, total_duration_ms=total, success=success)
