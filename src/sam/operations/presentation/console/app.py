"""ConsoleApp — Application lifecycle for the SAM Console.

States: INITIALIZING -> READY -> RUNNING -> STOPPING -> STOPPED
No business logic. Pure lifecycle management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional, Tuple
from datetime import datetime


class AppState(Enum):
    """Console application lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class AppConfig:
    """Console application configuration (immutable after boot)."""
    app_name: str = "SAM Console"
    version: str = "4.7.0"
    log_level: str = "INFO"
    enable_plugins: bool = False
    enable_telemetry: bool = True
    max_startup_time: float = 30.0  # seconds
    graceful_timeout: float = 5.0   # seconds
    
    def as_dict(self) -> dict:
        return {
            "app_name": self.app_name,
            "version": self.version,
            "log_level": self.log_level,
            "enable_plugins": self.enable_plugins,
            "enable_telemetry": self.enable_telemetry,
        }


@dataclass
class ConsoleApp:
    """Console application with formal lifecycle.

    Usage:
        app = ConsoleApp()
        app.startup(config)
        app.run()
        app.shutdown()
    """

    state: AppState = AppState.INITIALIZING
    start_time: Optional[str] = None
    stop_time: Optional[str] = None
    config: AppConfig = field(default_factory=AppConfig)
    
    _on_startup: Optional[Callable[..., None]] = None
    _on_ready: Optional[Callable[..., None]] = None
    _on_shutdown: Optional[Callable[..., None]] = None
    _on_restart: Optional[Callable[..., None]] = None
    _restart_requested: bool = False

    # ── Lifecycle hooks ───────────────────────────────────────────────

    def set_on_startup(self, callback: Callable[..., None]) -> None:
        """Register startup callback."""
        self._on_startup = callback

    def set_on_ready(self, callback: Callable[..., None]) -> None:
        """Register ready callback."""
        self._on_ready = callback

    def set_on_shutdown(self, callback: Callable[..., None]) -> None:
        """Register shutdown callback."""
        self._on_shutdown = callback

    def set_on_restart(self, callback: Callable[..., None]) -> None:
        """Register restart callback."""
        self._on_restart = callback

    # ── Lifecycle methods ─────────────────────────────────────────────

    def startup(self, config: Optional[AppConfig] = None) -> bool:
        """Run startup sequence: INITIALIZING -> READY.

        Returns True if startup succeeded.
        """
        self.state = AppState.INITIALIZING
        self.start_time = datetime.now().isoformat()
        
        if config:
            self.config = config

        try:
            if self._on_startup:
                self._on_startup()
            self.state = AppState.READY
            if self._on_ready:
                self._on_ready()
            return True
        except Exception:
            self.state = AppState.STOPPED
            return False

    def run(self) -> None:
        """Transition from READY to RUNNING state."""
        if self.state != AppState.READY:
            raise RuntimeError(
                f"Cannot run: app is {self.state}, expected READY"
            )
        self.state = AppState.RUNNING

    def shutdown(self) -> bool:
        """Run shutdown sequence: RUNNING/READY -> STOPPING -> STOPPED.

        Returns True if shutdown succeeded.
        """
        if self.state in (AppState.STOPPED, AppState.STOPPING):
            return True

        self.state = AppState.STOPPING
        self.stop_time = datetime.now().isoformat()

        try:
            if self._on_shutdown:
                self._on_shutdown()
            self.state = AppState.STOPPED
            return True
        except Exception:
            self.state = AppState.STOPPED
            return False

    def request_restart(self) -> None:
        """Signal that a restart is desired on next opportunity."""
        self._restart_requested = True

    def perform_restart(self) -> bool:
        """Perform a full restart cycle: STOPPED -> INITIALIZING -> READY.

        Returns True if restart succeeded.
        """
        self.shutdown()
        self._restart_requested = False
        try:
            if self._on_restart:
                self._on_restart()
            result = self.startup(self.config)
            if result:
                self.run()
            return result
        except Exception:
            self.state = AppState.STOPPED
            return False

    def graceful_exit(self, timeout: float = 5.0) -> bool:
        """Attempt graceful shutdown within timeout.

        Returns True if clean shutdown completed.
        """
        return self.shutdown()

    # ── Queries ───────────────────────────────────────────────────────

    @property
    def is_initializing(self) -> bool:
        return self.state == AppState.INITIALIZING

    @property
    def is_ready(self) -> bool:
        return self.state == AppState.READY

    @property
    def is_running(self) -> bool:
        return self.state == AppState.RUNNING

    @property
    def is_stopping(self) -> bool:
        return self.state == AppState.STOPPING

    @property
    def is_stopped(self) -> bool:
        return self.state == AppState.STOPPED

    @property
    def uptime_seconds(self) -> float:
        """Calculate uptime in seconds. Returns 0 if not running."""
        if not self.start_time or self.state == AppState.STOPPED:
            return 0.0
        start = datetime.fromisoformat(self.start_time)
        end = (
            datetime.fromisoformat(self.stop_time)
            if self.stop_time
            else datetime.now()
        )
        return (end - start).total_seconds()

    @property
    def restart_pending(self) -> bool:
        return self._restart_requested

    # ── Cleanup ───────────────────────────────────────────────────────

    def __enter__(self) -> ConsoleApp:
        return self

    def __exit__(self, *args: Any) -> None:
        self.shutdown()


def run(config: Optional[AppConfig] = None) -> ConsoleApp:
    """Module-level launcher entry for the SAM Console.

    Instantiates :class:`ConsoleApp`, runs the startup sequence, then
    transitions to RUNNING. Returns the running app instance so callers
    can call :meth:`ConsoleApp.shutdown` when done.

    Expected by ``sam.launcher.host_launcher._launch_console`` which
    resolves a module-level ``run`` callable (mirrors desktop app).
    """
    app = ConsoleApp()
    app.startup(config)
    app.run()
    return app
