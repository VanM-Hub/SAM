"""DesktopApplication — Application lifecycle for the SAM Desktop.

States: INITIALIZING -> READY -> RUNNING -> STOPPING -> STOPPED
No business logic. Pure lifecycle management.
Desktop is a consumer host — not a domain layer.

Mirrors ConsoleApp (OP-181) pattern for desktop context.
ConsoleApp and DesktopApplication are independent hosts.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Optional
from datetime import datetime


class DesktopAppState(Enum):
    """Desktop application lifecycle states."""
    INITIALIZING = "initializing"
    READY = "ready"
    RUNNING = "running"
    STOPPING = "stopping"
    STOPPED = "stopped"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class DesktopConfig:
    """Desktop application configuration (immutable after boot).

    Desktop-only settings. ConsoleConfig handles console-specific settings.
    Both are independent.
    """
    app_name: str = "SAM Desktop"
    version: str = "4.9.0"
    log_level: str = "INFO"
    enable_notifications: bool = True
    enable_system_tray: bool = True
    enable_log_panel: bool = True
    startup_maximized: bool = False
    graceful_timeout: float = 5.0

    def as_dict(self) -> dict:
        return {
            "app_name": self.app_name,
            "version": self.version,
            "log_level": self.log_level,
            "enable_notifications": self.enable_notifications,
            "enable_system_tray": self.enable_system_tray,
        }


@dataclass
class DesktopApplication:
    """Desktop application with formal lifecycle.

    DesktopApplication is a host for ConsoleSession.
    It does NOT duplicate ConsoleApp — both are independent hosts.

    Usage:
        app = DesktopApplication()
        app.startup(config)
        app.run()
        app.shutdown()
    """

    state: DesktopAppState = DesktopAppState.INITIALIZING
    start_time: Optional[str] = None
    stop_time: Optional[str] = None
    config: DesktopConfig = field(default_factory=DesktopConfig)

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

    def startup(self, config: Optional[DesktopConfig] = None) -> bool:
        """Run startup sequence: INITIALIZING -> READY.

        Returns True if startup succeeded.
        """
        self.state = DesktopAppState.INITIALIZING
        self.start_time = datetime.now().isoformat()

        if config:
            self.config = config

        try:
            if self._on_startup:
                self._on_startup()
            self.state = DesktopAppState.READY
            if self._on_ready:
                self._on_ready()
            return True
        except Exception:
            self.state = DesktopAppState.STOPPED
            return False

    def run(self) -> None:
        """Transition from READY to RUNNING state."""
        if self.state != DesktopAppState.READY:
            raise RuntimeError(
                f"Cannot run: app is {self.state}, expected READY"
            )
        self.state = DesktopAppState.RUNNING

    def shutdown(self) -> bool:
        """Run shutdown sequence: RUNNING/READY -> STOPPING -> STOPPED.

        Returns True if shutdown succeeded.
        """
        if self.state in (DesktopAppState.STOPPED, DesktopAppState.STOPPING):
            return True

        self.state = DesktopAppState.STOPPING
        self.stop_time = datetime.now().isoformat()

        try:
            if self._on_shutdown:
                self._on_shutdown()
            self.state = DesktopAppState.STOPPED
            return True
        except Exception:
            self.state = DesktopAppState.STOPPED
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
            self.state = DesktopAppState.STOPPED
            return False

    def graceful_exit(self, timeout: float = 5.0) -> bool:
        """Attempt graceful shutdown within timeout.

        Returns True if clean shutdown completed.
        """
        return self.shutdown()

    # ── Queries ───────────────────────────────────────────────────────

    @property
    def is_initializing(self) -> bool:
        return self.state == DesktopAppState.INITIALIZING

    @property
    def is_ready(self) -> bool:
        return self.state == DesktopAppState.READY

    @property
    def is_running(self) -> bool:
        return self.state == DesktopAppState.RUNNING

    @property
    def is_stopping(self) -> bool:
        return self.state == DesktopAppState.STOPPING

    @property
    def is_stopped(self) -> bool:
        return self.state == DesktopAppState.STOPPED

    @property
    def uptime_seconds(self) -> float:
        """Calculate uptime in seconds. Returns 0 if not running."""
        if not self.start_time or self.state == DesktopAppState.STOPPED:
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

    # ── Context manager ───────────────────────────────────────────────

    def __enter__(self) -> DesktopApplication:
        return self

    def __exit__(self, *args: Any) -> None:
        self.shutdown()
