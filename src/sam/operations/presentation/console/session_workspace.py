"""SessionWorkspace — Session workspace for the SAM Console.

Shows session info, current context, selected mission, navigation history,
command history, and active filters. Read-only view model composition.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple


@dataclass(frozen=True)
class SessionWorkspace:
    """Session workspace view model (immutable).

    Read-only snapshot of current session state.
    All data is composed from view models, not domain objects.
    """

    # Session info
    session_id: str = ""
    app_name: str = ""
    app_version: str = ""
    started_at: str = ""
    uptime_seconds: float = 0.0

    # Current context
    active_screen: str = "dashboard"
    previous_screen: str = ""
    refresh_mode: str = "manual"
    current_theme: str = "dark"

    # Selected mission
    selected_mission_id: str = ""
    selected_mission_name: str = ""

    # Navigation history
    navigation_history: Tuple[str, ...] = ()
    command_history: Tuple[str, ...] = ()

    # Active filters
    search_filter: str = ""
    status_filter: str = "all"
    sort_by: str = "newest"
    current_page: int = 1

    # Status
    error_count: int = 0
    render_count: int = 0
    notification_count: int = 0

    # ── Queries ──────────────────────────────────────────────────────

    @property
    def has_selected_mission(self) -> bool:
        return bool(self.selected_mission_id)

    @property
    def session_summary(self) -> str:
        return (
            f"Session: {self.session_id or 'N/A'} | "
            f"App: {self.app_name} v{self.app_version} | "
            f"Screen: {self.active_screen} | "
            f"Uptime: {self.uptime_seconds:.0f}s"
        )


# ── Factory ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class SessionWorkspaceFactory:
    """Builds SessionWorkspace from existing runtime state.

    Composes data from dashboard, session, and telemetry objects.
    """

    @staticmethod
    def compose(
        session_id: str = "",
        app_name: str = "SAM Console",
        app_version: str = "4.8.0",
        started_at: str = "",
        uptime_seconds: float = 0.0,
        active_screen: str = "dashboard",
        previous_screen: str = "",
        refresh_mode: str = "manual",
        current_theme: str = "dark",
        selected_mission_id: str = "",
        selected_mission_name: str = "",
        navigation_history: Tuple[str, ...] = (),
        command_history: Tuple[str, ...] = (),
        search_filter: str = "",
        status_filter: str = "all",
        sort_by: str = "newest",
        current_page: int = 1,
        error_count: int = 0,
        render_count: int = 0,
        notification_count: int = 0,
    ) -> SessionWorkspace:
        """Build SessionWorkspace from individual parameters."""
        return SessionWorkspace(
            session_id=session_id,
            app_name=app_name,
            app_version=app_version,
            started_at=started_at,
            uptime_seconds=uptime_seconds,
            active_screen=active_screen,
            previous_screen=previous_screen,
            refresh_mode=refresh_mode,
            current_theme=current_theme,
            selected_mission_id=selected_mission_id,
            selected_mission_name=selected_mission_name,
            navigation_history=navigation_history,
            command_history=command_history,
            search_filter=search_filter,
            status_filter=status_filter,
            sort_by=sort_by,
            current_page=current_page,
            error_count=error_count,
            render_count=render_count,
            notification_count=notification_count,
        )

    @staticmethod
    def from_runtime(
        dashboard_runtime: object = None,
        app: object = None,
        telemetry: object = None,
        notification_workspace: object = None,
        command_history: Tuple[str, ...] = (),
        navigation_history: Tuple[str, ...] = (),
    ) -> SessionWorkspace:
        """Build SessionWorkspace from runtime objects.

        Uses getattr for safe access — 0 assumptions about internals.
        """
        screen = "dashboard"
        prev_screen = ""
        refresh_mode = "manual"
        sel_mission = ""
        sel_mission_name = ""
        search_filter = ""
        status_filter = "all"
        sort_by = "newest"
        current_page = 1

        if dashboard_runtime is not None:
            screen = getattr(dashboard_runtime, 'active_screen', screen)
            prev_screen = getattr(dashboard_runtime, 'previous_screen', '')
            refresh_mode = str(getattr(
                dashboard_runtime, 'refresh_mode', 'manual'
            ))
            fs = getattr(dashboard_runtime, 'filter_state', None)
            if fs is not None:
                search_filter = getattr(fs, 'search', '')
                status_filter = getattr(fs, 'status_filter', 'all')
                sort_by = getattr(fs, 'sort_by', 'newest')
                current_page = getattr(fs, 'page', 1)

        app_name = "SAM Console"
        app_version = "4.8.0"
        started_at = ""
        session_id = ""
        if app is not None:
            app_name = getattr(app, 'app_name', app_name)
            app_version = getattr(getattr(app, 'config', None), 'version', app_version)
            started_at = getattr(app, 'start_time', '')
            session_id = getattr(app, 'session_id', '')

        uptime = 0.0
        error_count = 0
        render_count = 0
        if telemetry is not None:
            uptime = getattr(telemetry, 'uptime_seconds', 0.0)
            error_count = getattr(telemetry, 'error_count', 0)
            render_count = getattr(telemetry, 'render_count', 0)

        notif_count = 0
        if notification_workspace is not None:
            notif_count = getattr(notification_workspace, 'unread_count', 0)

        return SessionWorkspace(
            session_id=session_id,
            app_name=app_name,
            app_version=app_version,
            started_at=started_at,
            uptime_seconds=uptime,
            active_screen=screen,
            previous_screen=prev_screen,
            refresh_mode=refresh_mode,
            selected_mission_id=sel_mission,
            selected_mission_name=sel_mission_name,
            navigation_history=navigation_history,
            command_history=command_history,
            search_filter=search_filter,
            status_filter=status_filter,
            sort_by=sort_by,
            current_page=current_page,
            error_count=error_count,
            render_count=render_count,
            notification_count=notif_count,
        )

    @staticmethod
    def empty() -> SessionWorkspace:
        return SessionWorkspace()
