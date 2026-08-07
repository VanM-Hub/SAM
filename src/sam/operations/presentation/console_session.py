"""ConsoleSession — Orchestrates Console renderer, navigation, refresh, dispatcher, and theme.

This is the main entry point for the SAM Console runtime.
It connects all Presentation Layer components together.
No business logic. No domain access. No database.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Optional, List, Tuple
from datetime import datetime

import sam as _sam_pkg

from .console_view import ConsoleView, HeaderView, SidebarView, BodyView, StatusBarView, FooterView
from .console_renderer import ConsoleRenderer
from .widget_renderer import WidgetRenderer
from .navigation_runtime import NavigationRuntime, NavigationMenu
from .live_refresh import LiveRefresh
from .dispatcher import CommandDispatcher, CommandResult, CommandHistory
from .theme_runtime import ThemeRuntime
from .theme import Theme, DarkTheme, LightTheme
from .navigation import (
    DASHBOARD, MISSIONS, APPROVALS, TIMELINE, TRUST, HISTORY, SETTINGS, HELP,
)
from .dashboard_composer import ConsoleDashboard, DashboardComposer
from .widgets import WidgetRegistry


def _console_version() -> str:
    """Resolve the SAM console version from the single package source."""
    try:
        return str(getattr(_sam_pkg, "__version__", "1.0.0"))
    except Exception:
        return "1.0.0"


@dataclass
class ConsoleSession:
    """Orchestrates the full Console experience.

    Usage:
        session = ConsoleSession()
        session.start()
        session.update_dashboard(dashboard)
        session.render()
        session.handle_input("approve mission_123")
        session.stop()
    """

    renderer: ConsoleRenderer = field(default_factory=ConsoleRenderer)
    widget_renderer: WidgetRenderer = field(default_factory=WidgetRenderer)
    navigation: NavigationRuntime = field(default_factory=NavigationRuntime)
    refresh: LiveRefresh = field(default_factory=LiveRefresh)
    dispatcher: CommandDispatcher = field(default_factory=CommandDispatcher)
    theme: ThemeRuntime = field(default_factory=ThemeRuntime)

    _running: bool = False
    _current_dashboard: Optional[ConsoleDashboard] = None
    _current_widgets: Optional[WidgetRegistry] = None
    _composer: DashboardComposer = field(default_factory=DashboardComposer)

    def __post_init__(self) -> None:
        self._running = False
        self._current_dashboard = None
        self._current_widgets = None
        # Update renderer theme
        object.__setattr__(self.renderer, "theme", self.theme.current)

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the console session."""
        self._running = True
        self.navigation.go_home()

    def stop(self) -> None:
        """Stop the console session."""
        self._running = False

    @property
    def is_running(self) -> bool:
        return self._running

    # ── Data update flow ──────────────────────────────────────────────

    def update_dashboard(self, dashboard: ConsoleDashboard) -> None:
        """Update the current dashboard data."""
        self._current_dashboard = dashboard
        self.refresh.mark_dirty("full")

    def update_widgets(self, registry: WidgetRegistry) -> None:
        """Update the current widget registry."""
        self._current_widgets = registry
        self.refresh.mark_dirty("full")

    def compose_and_update(self, **dto_kwargs: Any) -> ConsoleDashboard:
        """Compose DTOs into a dashboard and update the session.

        This is the primary integration point:
            session.compose_and_update(
                mission_dto=...,
                action_dto=...,
                notification_store=...,
                summary=...,
            )
        """
        dashboard = self._composer.compose(**dto_kwargs)
        self.update_dashboard(dashboard)
        return dashboard

    # ── Rendering ─────────────────────────────────────────────────────

    def render(self) -> None:
        """Render the current screen based on navigation state."""
        if not self._running:
            return

        screen = self.navigation.state.active_screen
        menu = self.navigation.menu
        nav = self.navigation.state

        # Build view model
        header = self._build_header(screen, menu)
        sidebar = self._build_sidebar(menu, nav)
        body = self._build_body(screen)
        status_bar = self._build_status_bar()
        footer = self._build_footer(menu)

        view = ConsoleView(
            header=header,
            sidebar=sidebar,
            body=body,
            status_bar=status_bar,
            footer=footer,
        )

        self.renderer.render_console_view(view, nav, self._current_widgets)

    def render_dashboard_only(self) -> None:
        """Render just the dashboard content."""
        if self._current_dashboard:
            self.renderer.render_dashboard(self._current_dashboard)

    def render_widget(self, widget_type: str, data: Any) -> None:
        """Render a single widget."""
        self.renderer.render_widget(widget_type, data)

    # ── Input handling ────────────────────────────────────────────────

    def handle_input(self, line: str) -> CommandResult:
        """Parse and execute a user input line.

        Returns CommandResult with screen_change if navigation is needed.
        """
        line = line.strip()
        if not line:
            return CommandResult(success=True, message="", command_type="empty")

        parts = line.split(None, 1)
        command = parts[0] if parts else ""
        args = parts[1] if len(parts) > 1 else ""

        # Handle shortcuts
        if command == "?":
            command = "help"
        elif command in ("q", "quit"):
            command = "exit"
        elif command in ("r", "R"):
            command = "refresh"
        elif command in ("h", "back", "b"):
            command = "back"
        elif command in ("d", "home"):
            command = "home"
        elif command in ("1", "2", "3", "4", "5", "6", "7", "8", "9"):
            return self._handle_shortcut(command)

        result = self.dispatcher.dispatch(command, args)

        # Handle navigation results
        if result.screen_change == "exit":
            self.stop()
        elif result.screen_change == "back":
            self.navigation.go_back()
        elif result.screen_change == "dashboard":
            self.navigation.go_home()
        elif result.screen_change:
            self.navigation.navigate_to(result.screen_change)

        if result.command_type == "refresh":
            self._refresh_from_dispatch()

        return result

    def handle_interaction(self, interaction: Any) -> CommandResult:
        """Handle an Interaction Contract object directly."""
        result = self.dispatcher.dispatch_interaction(interaction)
        if result.command_type == "refresh":
            self._refresh_from_dispatch()
        return result

    # ── Theme ─────────────────────────────────────────────────────────

    def set_theme(self, theme_name: str) -> bool:
        """Switch theme by name (dark, light, minimal)."""
        success = self.theme.set_theme(theme_name)
        if success:
            object.__setattr__(self.renderer, "theme", self.theme.current)
        return success

    def cycle_theme(self) -> str:
        """Cycle to the next available theme."""
        name = self.theme.cycle()
        object.__setattr__(self.renderer, "theme", self.theme.current)
        return name

    # ── Navigation ────────────────────────────────────────────────────

    def navigate_to(self, screen: str) -> bool:
        """Navigate to a screen."""
        return self.navigation.navigate_to(screen)

    def go_back(self) -> bool:
        return self.navigation.go_back()

    def go_home(self) -> None:
        self.navigation.go_home()

    # ── Refresh ───────────────────────────────────────────────────────

    def tick(self, seconds_since_last: float = 0.0) -> None:
        """Called periodically to trigger refresh if needed."""
        if self.refresh.should_refresh(seconds_since_last):
            self.refresh.execute()

    def force_refresh(self) -> None:
        """Force a full refresh now."""
        self.refresh.mark_dirty("full")
        self.refresh.execute_all()

    # ── Internal view builders ────────────────────────────────────────

    def _build_header(self, screen: str, menu: NavigationMenu) -> HeaderView:
        status = "running" if self._running else "stopped"
        return HeaderView(
            title=f"SAM Console — {menu.screen_label}",
            subtitle=f"v{_console_version()} | {self.theme.current.name} theme",
            status=status,
            mode=self.refresh.mode.value,
        )

    def _build_sidebar(self, menu: NavigationMenu, nav: NavigationState) -> SidebarView:
        return SidebarView(
            active_screen=nav.active_screen,
            available_screens=("dashboard", "missions", "approvals", "timeline",
                               "trust", "history", "settings", "help"),
            notification_count=0,
            critical_alerts=0,
            current_mission="",
        )

    def _build_body(self, screen: str) -> BodyView:
        if screen == DASHBOARD and self._current_dashboard:
            d = self._current_dashboard
            return BodyView(
                content_type="dashboard",
                title="Operational Dashboard",
                summary=self._dashboard_summary_line(d),
                items=(
                    f"Missions: {d.total_missions} total, {d.running_missions} running",
                    f"Health:   {d.health_status} ({d.health_score:.1f})",
                    f"Trust:    {d.trust_grade} ({d.trust_score:.2f})",
                    f"Approvals: {d.pending_approvals} pending",
                    f"Notifications: {d.unread_notifications} unread",
                    f"Queue: {d.queue_size} items" if d.queue_size else "",
                ),
            )
        screen_labels = {
            MISSIONS: ("Missions", "View and manage active missions."),
            APPROVALS: ("Approvals", "Review pending approval requests."),
            TIMELINE: ("Timeline", "Browse operational event history."),
            TRUST: ("Trust", "Monitor trust scores and decision quality."),
            HISTORY: ("History", "Review past missions and decisions."),
            SETTINGS: ("Settings", "Configure console and system preferences."),
            HELP: ("Help", "Available commands and documentation."),
        }
        label, desc = screen_labels.get(screen, ("Console", ""))
        return BodyView(
            content_type="detail",
            title=f"{label} Screen",
            summary=desc,
            items=(f"Screen: {screen}", "Press '?' or type 'help' for commands."),
        )

    def _build_status_bar(self) -> StatusBarView:
        d = self._current_dashboard
        if d:
            return StatusBarView(
                mission_count=d.total_missions,
                pending_approvals=d.pending_approvals,
                trust_grade=d.trust_grade,
                health_status=d.health_status,
                last_event=d.generated_at[-8:] if d.generated_at else "",
            )
        return StatusBarView()

    def _build_footer(self, menu: NavigationMenu) -> FooterView:
        hints = [
            "1-8: Nav", "R: Refresh", "?: Help",
            f"Theme: {self.theme.current.name}",
            "Q: Exit",
        ]
        return FooterView(hints=tuple(hints), version=_console_version(),
                          mode=self.refresh.mode.value)

    @staticmethod
    def _dashboard_summary_line(d: ConsoleDashboard) -> str:
        return (f"{d.running_missions} running, {d.failed_missions} failed, "
                f"health={d.health_status}, trust={d.trust_grade}")

    def _handle_shortcut(self, key: str) -> CommandResult:
        """Handle numeric shortcut for navigation."""
        self.navigation.navigate_to_by_shortcut(key)
        if self.navigation.state.active_screen == "exit":
            self.stop()
            return CommandResult(success=True, message="Exiting...",
                                 command_type="exit", screen_change="exit")
        return CommandResult(success=True, message=f"Navigated to {self.navigation.state.screen_label}",
                             command_type="navigate")

    def _refresh_from_dispatch(self) -> None:
        """Refresh dashboard data after a dispatch command."""
        self.refresh.mark_dirty("full")
        self.render()
