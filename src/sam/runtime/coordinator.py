"""
Runtime Coordinator — Phase 1

State Machine + integrasi Bootstrap, Session, Shutdown, Recovery, Hosting, Telemetry.

Alur start:
  1. Set state = INITIALIZING
  2. Buat session baru
  3. Deteksi crash -> Recovery jika perlu
  4. Jalankan Bootstrap pipeline
  5. Jika sukses -> READY, jika gagal -> SAFE_MODE

Alur stop:
  1. Shutdown pipeline -> SHUTDOWN
"""

from typing import Optional
from datetime import datetime
from .state import RuntimeState
from .bootstrap import BootstrapManager
from .session import SessionManager
from .shutdown import ShutdownManager
from .recovery import RecoveryManager
from ..hosting.base import HostingAdapter, DesktopAdapter
from ..telemetry.service import TelemetryService
from ..telemetry.collector import MetricsCollector
from ..openclaw.discovery import OpenClawDiscovery
from ..openclaw.health import OpenClawHealthCollector, OpenClawStatus
from ..intelligence.detector import IncidentDetector
from ..intelligence.rca import RootCauseAnalyzer
from ..intelligence.recommender import Recommender
from ..intelligence.knowledge import KnowledgeLookup
from ..autonomous.executor import ActionExecutor
from ..autonomous.recovery import AutoRecovery
from ..autonomous.isolation import PluginIsolation
from .manifest import RuntimeManifest


class RuntimeCoordinator:
    """Runtime Coordinator — mengelola state, bootstrap, session, shutdown, recovery, hosting, telemetry."""

    def __init__(
        self,
        workspace_path: str = "./workspace",
        adapter: Optional[HostingAdapter] = None,
    ):
        self.state = RuntimeState.INITIALIZING
        self.workspace_path = workspace_path
        self.hosting_adapter = adapter or DesktopAdapter()
        self.session_manager = SessionManager(workspace_path)
        self.bootstrap_manager = BootstrapManager(self)
        self.shutdown_manager = ShutdownManager(self)
        self.recovery_manager = RecoveryManager(self)
        self.telemetry = TelemetryService()
        self.metrics_collector = MetricsCollector(self)
        self.start_time = None
        self.manifest = RuntimeManifest(workspace_path)
        self.openclaw_discovery = OpenClawDiscovery()
        self.openclaw_health = OpenClawHealthCollector()
        self.openclaw_workspace = None
        self.incident_detector = IncidentDetector(self.workspace_path)
        self.rca_analyzer = RootCauseAnalyzer()
        self.recommender = Recommender()
        self.knowledge_lookup = KnowledgeLookup()
        self.action_executor = ActionExecutor(self)
        self.auto_recovery = AutoRecovery(self)
        self.plugin_isolation = PluginIsolation(self)
        self.autonomous_enabled = True

    async def start(self) -> RuntimeState:
        self.state = RuntimeState.INITIALIZING
        self.start_time = datetime.utcnow()

        self.telemetry.emit_event(
            event_name="startup.initiating",
            runtime_state="initializing",
            component="coordinator",
        )

        self.session_manager.create_session(workspace=self.workspace_path)

        # OpenClaw Discovery
        try:
            workspaces = await self.openclaw_discovery.discover()
            if workspaces:
                self.openclaw_workspace = workspaces[0]
                self.telemetry.emit_event(
                    event_name="openclaw.discovered",
                    component="openclaw",
                    payload={"workspace": self.openclaw_workspace.path},
                )
                try:
                    health = await self.openclaw_health.collect(self.openclaw_workspace.path)
                    issues = await self.openclaw_health.detect_issues(health)
                    if issues:
                        for issue in issues:
                            self.telemetry.emit_event(
                                event_name="openclaw.issue",
                                severity="warning",
                                component="openclaw",
                                payload={"issue": issue},
                            )
                except Exception as health_err:
                    self.telemetry.emit_event(
                        event_name="openclaw.health_failed",
                        severity="warning",
                        component="openclaw",
                        payload={"error": str(health_err)},
                    )
            else:
                self.telemetry.emit_event(event_name="openclaw.not_found", component="openclaw")
        except Exception as discovery_err:
            self.telemetry.emit_event(
                event_name="openclaw.discovery_failed",
                severity="warning",
                component="openclaw",
                payload={"error": str(discovery_err)},
            )

        # Crash recovery check
        crash_detected = await self.recovery_manager._detect_crash()
        if crash_detected:
            self.telemetry.emit_event(
                event_name="startup.crash_detected", severity="warning",
                runtime_state="initializing", component="coordinator",
            )
            recovered = await self.recovery_manager.recover()
            if not recovered:
                self.state = RuntimeState.SAFE_MODE
                self.telemetry.emit_event(
                    event_name="startup.recovery_failed", severity="error",
                    runtime_state="safe_mode", component="coordinator",
                )
                return self.state

        # Bootstrap pipeline
        success = await self.bootstrap_manager.bootstrap()
        if success:
            self.state = RuntimeState.READY
            sess = self.session_manager.get_current_session()
            sess_id = sess["id"] if sess else ""
            self.telemetry.emit_event(
                event_name="startup.complete", runtime_state="ready",
                component="coordinator",
                payload={"state": self.state.value, "session_id": sess_id},
            )
        else:
            self.state = RuntimeState.SAFE_MODE
            self.telemetry.emit_event(
                event_name="startup.bootstrap_failed", severity="error",
                runtime_state="safe_mode", component="coordinator",
            )

        await self._update_manifest()
        return self.state

    async def run(self) -> RuntimeState:
        if self.state != RuntimeState.READY:
            raise RuntimeError("Cannot run from state: " + self.state.value)
        self.state = RuntimeState.RUNNING
        self.telemetry.emit_event(
            event_name="runtime.started", runtime_state="running", component="coordinator",
        )
        import asyncio
        asyncio.ensure_future(self.metrics_collector.start())
        await self._update_manifest()
        return self.state

    async def stop(self) -> RuntimeState:
        if self.state in (RuntimeState.SHUTDOWN, RuntimeState.CRASHED):
            return self.state
        self.telemetry.emit_event(
            event_name="runtime.stopping", runtime_state=self.state.value, component="coordinator",
        )
        await self.metrics_collector.stop()
        await self.shutdown_manager.shutdown()
        self.telemetry.emit_event(
            event_name="runtime.stopped", runtime_state="shutdown", component="coordinator",
        )
        await self._update_manifest()
        return self.state

    async def degrade(self) -> RuntimeState:
        if self.state != RuntimeState.RUNNING:
            raise RuntimeError("Cannot degrade from state: " + self.state.value)
        self.state = RuntimeState.DEGRADED
        await self._update_manifest()
        return self.state

    async def recover(self) -> RuntimeState:
        if self.state != RuntimeState.DEGRADED:
            raise RuntimeError("Cannot recover from state: " + self.state.value)
        self.state = RuntimeState.READY
        self.state = RuntimeState.RUNNING
        await self._update_manifest()
        return self.state

    @property
    def adapter_name(self) -> str:
        return self.hosting_adapter.__class__.__name__.replace("Adapter", "")

    async def _update_manifest(self) -> None:
        uptime = 0.0
        if self.start_time:
            uptime = (datetime.utcnow() - self.start_time).total_seconds()
        uptime = max(0.0, uptime)
        try:
            metrics = self.telemetry.get_metrics()
            health_score = metrics.health_score if metrics else 0.0
            if health_score >= 70:
                health_str = "HEALTHY"
            elif health_score >= 40:
                health_str = "DEGRADED"
            else:
                health_str = "UNHEALTHY"
        except Exception:
            health_str = "UNKNOWN"
        self.manifest.save({
            "runtime_version": "2.0.0",
            "workspace": self.workspace_path,
            "hosting": self.adapter_name.lower(),
            "state": self.state.value.upper(),
            "health": health_str,
            "uptime": int(uptime),
        })

    def __repr__(self) -> str:
        return "RuntimeCoordinator(state=" + self.state.value + ", adapter=" + self.adapter_name + ")"
