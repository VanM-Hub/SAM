"""StatusBar — Operational status bar view model for the SAM Console.

Pure view model. Shows current screen, refresh mode, connection state,
active missions, pending approvals, notification count, and theme.
No business logic. No rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


@dataclass(frozen=True)
class StatusBar:
    """Operational status bar — pure data.

    All fields are read-only. Composed from other view models.
    """

    # Screen
    screen: str = "dashboard"

    # Refresh
    refresh_mode: str = "manual"
    is_paused: bool = False

    # Connection
    connection: str = "connected"  # connected, disconnected, reconnecting
    connection_detail: str = ""

    # Missions
    active_missions: int = 0
    total_missions: int = 0

    # Approvals
    pending_approvals: int = 0
    critical_approvals: int = 0

    # Notifications
    notification_count: int = 0
    unread_notifications: int = 0

    # Theme / Mode
    current_theme: str = "dark"
    is_plain_mode: bool = False
    is_safe_mode: bool = False

    # System
    uptime_seconds: float = 0.0
    render_count: int = 0
    error_count: int = 0
    memory_hint: str = ""

    def __post_init__(self) -> None:
        """Validates status bar fields (no-op for frozen)."""
        pass

    # ── Display helpers ──────────────────────────────────────────────

    @property
    def refresh_indicator(self) -> str:
        if self.is_paused:
            return "PAUSED"
        return self.refresh_mode.upper()

    @property
    def connection_indicator(self) -> str:
        if self.connection == "connected":
            return "ON"
        elif self.connection == "reconnecting":
            return "R"
        return "OFF"

    @property
    def theme_indicator(self) -> str:
        if self.is_safe_mode:
            return f"{self.current_theme} SAFE"
        if self.is_plain_mode:
            return f"{self.current_theme} PLAIN"
        return self.current_theme

    @property
    def line_parts(self) -> tuple:
        """Returns status bar components for composable rendering."""
        return (
            f"Screen: {self.screen}",
            f"Ref: {self.refresh_indicator}",
            f"Conn: {self.connection_indicator}",
            f"Missions: {self.active_missions}/{self.total_missions}",
            f"Approvals: {self.pending_approvals}",
            f"Notif: {self.notification_count}",
            f"Theme: {self.theme_indicator}",
        )

    @property
    def compact_line(self) -> str:
        """Single-line compact status."""
        return (
            f"{self.screen} | {self.refresh_indicator} "
            f"| {self.connection_indicator} "
            f"| M:{self.active_missions}/{self.total_missions} "
            f"| A:{self.pending_approvals} "
            f"| N:{self.notification_count} "
            f"| {self.theme_indicator}"
        )

    @property
    def full_line(self) -> str:
        full = (
            f"Screen: {self.screen} | "
            f"Refresh: {self.refresh_indicator} | "
            f"Connection: {self.connection_indicator} | "
            f"Missions: {self.active_missions}/{self.total_missions} | "
            f"Approvals: {self.pending_approvals} | "
            f"Notif: {self.notification_count} | "
            f"Theme: {self.theme_indicator}"
        )
        if self.error_count > 0:
            full += f" | Errors: {self.error_count}"
        return full


# ── Factory ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class StatusBarFactory:
    """Composes a StatusBar from multiple view models.

    This is the ONLY place that aggregates data for the status bar.
    """

    @staticmethod
    def compose(
        screen: str = "dashboard",
        refresh_mode: str = "manual",
        is_paused: bool = False,
        dashboard: object = None,
        mission_monitor: object = None,
        approval_workspace: object = None,
        notification_workspace: object = None,
        theme: str = "dark",
        is_plain_mode: bool = False,
        is_safe_mode: bool = False,
        telemetry: object = None,
        connection: str = "connected",
        uptime_seconds: float = 0.0,
    ) -> StatusBar:
        """Build StatusBar from available view models and runtime state."""
        active = 0
        total = 0
        if mission_monitor is not None:
            active = getattr(mission_monitor, 'active_count',
                             getattr(mission_monitor, 'running', 0))
            active += getattr(mission_monitor, 'pending', 0)
            total = getattr(mission_monitor, 'total', 0)

        pending_app = 0
        critical_app = 0
        if approval_workspace is not None:
            pending_app = getattr(approval_workspace, 'total_pending', 0)
            critical_app = getattr(approval_workspace, 'critical_pending', 0)

        notif_count = 0
        unread = 0
        if notification_workspace is not None:
            notif_count = getattr(notification_workspace, 'unread_count', 0)
            unread = getattr(notification_workspace, 'unread_count', 0)

        render_count = 0
        error_count = 0
        if telemetry is not None:
            render_count = getattr(telemetry, 'render_count', 0)
            error_count = getattr(telemetry, 'error_count', 0)

        return StatusBar(
            screen=screen,
            refresh_mode=refresh_mode,
            is_paused=is_paused,
            connection=connection,
            active_missions=active,
            total_missions=total,
            pending_approvals=pending_app,
            critical_approvals=critical_app,
            notification_count=notif_count,
            unread_notifications=unread,
            current_theme=theme,
            is_plain_mode=is_plain_mode,
            is_safe_mode=is_safe_mode,
            uptime_seconds=uptime_seconds,
            render_count=render_count,
            error_count=error_count,
        )
