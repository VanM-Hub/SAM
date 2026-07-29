"""
OP-373 — Host Launcher

Menjalankan host berdasarkan HostType:

  CONSOLE   → sam.operations.presentation.console
  DESKTOP   → sam.desktop.main
  HEADLESS  → Telemetry + Health server via asyncio
  API_SERVER → sam.api.server
  TESTING   → No-op
  DIAGNOSTICS → DiagnosticsEngine standalone

Semua path menggunakan importlib — tidak ada import langsung.
"""

import os
import sys
import asyncio
import threading
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Callable
from importlib import import_module

from sam.launcher.host_manager import HostType


@dataclass(frozen=True)
class HostLaunchResult:
    """Result of a host launch attempt."""

    host_type: str
    success: bool
    pid: int = 0
    error: str = ""
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "host_type": self.host_type,
            "success": self.success,
            "pid": self.pid,
            "error": self.error,
            "duration_ms": self.duration_ms,
        }


class HostLauncher:
    """Launches and manages host processes.

    All launches go through importlib for safety.
    """

    def __init__(self, workspace: str = "") -> None:
        self._workspace = workspace or os.getcwd()
        self._launch_fns: Dict[HostType, Callable[[], bool]] = {
            HostType.CONSOLE: self._launch_console,
            HostType.DESKTOP: self._launch_desktop,
            HostType.HEADLESS: self._launch_headless,
            HostType.API_SERVER: self._launch_api_server,
            HostType.TESTING: self._launch_testing,
            HostType.DIAGNOSTICS: self._launch_diagnostics,
        }

    def launch(self, host_type: HostType) -> HostLaunchResult:
        """Launch a host by type.

        Returns immediately for interactive hosts (console, desktop).
        Blocks for server hosts (headless, api_server).
        """
        import time
        start = time.perf_counter()
        fn = self._launch_fns.get(host_type)
        if not fn:
            dur = (time.perf_counter() - start) * 1000
            return HostLaunchResult(
                host_type=host_type.value,
                success=False,
                error=f"Unknown host type: {host_type}",
                duration_ms=round(dur, 1),
            )
        try:
            success = fn()
            dur = (time.perf_counter() - start) * 1000
            return HostLaunchResult(
                host_type=host_type.value,
                success=success,
                pid=os.getpid(),
                duration_ms=round(dur, 1),
            )
        except Exception as exc:
            dur = (time.perf_counter() - start) * 1000
            return HostLaunchResult(
                host_type=host_type.value,
                success=False,
                error=str(exc),
                duration_ms=round(dur, 1),
            )

    # ── individual launchers ──

    def _launch_console(self) -> bool:
        # Console via importlib
        mod = import_module("sam.operations.presentation.console.app")
        # The console app usually has a main or run function
        run_fn = getattr(mod, "run", None)
        if run_fn:
            run_fn()
            return True
        return False

    def _launch_desktop(self) -> bool:
        # Desktop via importlib
        mod = import_module("sam.desktop.main")
        run_fn = getattr(mod, "run", None)
        if run_fn:
            run_fn()
            return True
        return False

    def _launch_headless(self) -> bool:
        # Telemetry + Health server via importlib
        mod = import_module("sam.telemetry.service")
        health_mod = import_module("sam.operations.health")
        TelemetryService = getattr(mod, "TelemetryService")
        HealthServer = getattr(health_mod, "HealthServer")

        async def _run():
            telemetry = TelemetryService()
            server = HealthServer()
            await telemetry.start()
            server.mark_ready(telemetry=True)
            await server.start()
            try:
                await asyncio.Event().wait()
            except (KeyboardInterrupt, asyncio.CancelledError):
                await server.stop()
                await telemetry.stop()

        asyncio.run(_run())
        return True

    def _launch_api_server(self) -> bool:
        mod = import_module("sam.api.server")
        run_fn = getattr(mod, "run", None)
        if run_fn:
            run_fn()
            return True
        return False

    def _launch_testing(self) -> bool:
        # Testing mode — no host to launch
        import logging
        logging.getLogger("sam.launcher").info("Testing mode — no host launched")
        return True

    def _launch_diagnostics(self) -> bool:
        from sam.launcher.diagnostics import DiagnosticsEngine
        engine = DiagnosticsEngine(self._workspace)
        snap = engine.snapshot()
        # Print brief report
        print("=" * 48)
        print(f"  Diagnostics Report — {snap.summary.total_checks} checks")
        print(f"  Passed: {snap.summary.passed}")
        print(f"  Failed: {snap.summary.failed}")
        print(f"  Elapsed: {snap.summary.elapsed:.2f}s")
        print("=" * 48)
        return True
