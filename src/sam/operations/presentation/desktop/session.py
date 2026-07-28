"""DesktopSession — Bridges ConsoleSession into the Desktop runtime.

DesktopSession connects the Presentation orchestrator (ConsoleSession)
with the DesktopApplication lifecycle. It does NOT duplicate session
state — ConsoleSession is the single source of truth for presentation.

No business logic. No domain access. Only orchestration.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Optional, List, Tuple
from datetime import datetime


@dataclass(frozen=True)
class DesktopSessionState:
    """Read-only snapshot of desktop session state.

    Bridged from ConsoleSession state. No duplication.
    """
    running: bool = False
    active_screen: str = "dashboard"
    current_theme: str = "dark"
    uptime_seconds: float = 0.0
    last_render_time: str = ""
    error_message: str = ""


@dataclass
class DesktopSession:
    """Bridges ConsoleSession to Desktop runtime.

    DesktopSession does NOT wrap or duplicate ConsoleSession.
    It provides the integration seams needed by Desktop widgets.

    Usage:
        session = DesktopSession()
        session.attach_console_session(console_session)
        session.start()
        session.update_view()
        session.stop()
    """

    _console_session: Any = None
    _running: bool = False
    _start_time: Optional[str] = None
    _last_error: Optional[str] = None

    _on_view_changed: List[Callable[[DesktopSessionState], None]] = field(default_factory=list)
    _on_screen_changed: List[Callable[[str], None]] = field(default_factory=list)
    _on_theme_changed: List[Callable[[str], None]] = field(default_factory=list)

    # ── Attach ────────────────────────────────────────────────────────

    def attach_console_session(self, console_session: Any) -> None:
        """Attach a ConsoleSession instance.

        ConsoleSession is the single source of truth for
        presentation orchestration. DesktopSession reads from it.
        """
        self._console_session = console_session

    @property
    def console_session(self) -> Any:
        return self._console_session

    # ── Lifecycle ─────────────────────────────────────────────────────

    def start(self) -> bool:
        """Start the desktop session.

        Initializes ConsoleSession if attached.
        Returns True if startup succeeded.
        """
        if self._console_session is None:
            self._last_error = "No ConsoleSession attached"
            return False

        self._start_time = datetime.now().isoformat()
        try:
            self._console_session.start()
            self._running = True
            self._notify_view_changed()
            return True
        except Exception as e:
            self._last_error = str(e)
            self._running = False
            return False

    def stop(self) -> bool:
        """Stop the desktop session.

        Stops ConsoleSession gracefully.
        Returns True if shutdown succeeded.
        """
        if not self._running:
            return True

        try:
            if self._console_session:
                self._console_session.stop()
            self._running = False
            return True
        except Exception as e:
            self._last_error = str(e)
            self._running = False
            return False

    # ── State bridging ────────────────────────────────────────────────

    @property
    def state(self) -> DesktopSessionState:
        """Get a read-only snapshot of current session state."""
        if self._console_session is None:
            return DesktopSessionState(running=self._running)

        cs = self._console_session
        screen = getattr(cs, '_current_screen', 'dashboard')
        theme_name = "dark"
        theme = getattr(cs, 'theme', None)
        if theme:
            theme_name = getattr(theme, 'active_name', 'dark')

        uptime = 0.0
        start = getattr(cs, '_start_time', None)
        if start:
            try:
                st = datetime.fromisoformat(start)
                uptime = (datetime.now() - st).total_seconds()
            except (ValueError, TypeError):
                pass

        # Get screen from navigation
        nav = getattr(cs, 'navigation', None)
        if nav:
            nav_state = getattr(nav, 'state', None)
            if nav_state:
                screen = getattr(nav_state, 'active_screen', screen)

        last_render = self._start_time or ""

        return DesktopSessionState(
            running=self._running,
            active_screen=screen,
            current_theme=theme_name,
            uptime_seconds=uptime,
            last_render_time=last_render,
            error_message=self._last_error or "",
        )

    # ── View update ───────────────────────────────────────────────────

    def update_view(self) -> None:
        """Trigger a view update through ConsoleSession."""
        if not self._running or self._console_session is None:
            return
        try:
            self._console_session.render()
            self._notify_view_changed()
        except Exception as e:
            self._last_error = str(e)

    def navigate(self, screen: str) -> bool:
        """Navigate to a screen via ConsoleSession.

        Returns True if navigation succeeded.
        """
        if self._console_session is None:
            return False
        try:
            nav = getattr(self._console_session, 'navigation', None)
            if nav:
                result = getattr(nav, 'navigate_to', lambda s: False)(screen)
                if result:
                    self._on_screen_changed_cb(screen)
                return result
            return False
        except Exception as e:
            self._last_error = str(e)
            return False

    def go_home(self) -> bool:
        """Navigate to dashboard."""
        if self._console_session is None:
            return False
        try:
            nav = getattr(self._console_session, 'navigation', None)
            if nav:
                getattr(nav, 'go_home', lambda: None)()
                self._on_screen_changed_cb("dashboard")
                return True
            return False
        except Exception:
            return False

    def set_theme(self, theme_name: str) -> bool:
        """Set theme via ConsoleSession.

        Uses getattr for safe access.
        """
        if self._console_session is None:
            return False
        try:
            setter = getattr(self._console_session, 'set_theme', None)
            if setter:
                result = setter(theme_name)
                if result:
                    self._on_theme_changed_cb(theme_name)
                return result
            return False
        except Exception as e:
            self._last_error = str(e)
            return False

    def cycle_theme(self) -> str:
        """Cycle to the next theme via ConsoleSession."""
        if self._console_session is None:
            return "dark"
        try:
            cycler = getattr(self._console_session, 'cycle_theme', None)
            if cycler:
                return cycler()
            return "dark"
        except Exception:
            return "dark"

    # ── Event hooks ───────────────────────────────────────────────────

    def on_view_changed(self, callback: Callable[[DesktopSessionState], None]) -> None:
        """Register view change callback."""
        self._on_view_changed.append(callback)

    def on_screen_changed(self, callback: Callable[[str], None]) -> None:
        """Register screen change callback."""
        self._on_screen_changed.append(callback)

    def on_theme_changed(self, callback: Callable[[str], None]) -> None:
        """Register theme change callback."""
        self._on_theme_changed.append(callback)

    # ── Internal ──────────────────────────────────────────────────────

    def _notify_view_changed(self) -> None:
        state = self.state
        for cb in self._on_view_changed:
            try:
                cb(state)
            except Exception:
                pass

    def _on_screen_changed_cb(self, screen: str) -> None:
        for cb in self._on_screen_changed:
            try:
                cb(screen)
            except Exception:
                pass

    def _on_theme_changed_cb(self, theme: str) -> None:
        for cb in self._on_theme_changed:
            try:
                cb(theme)
            except Exception:
                pass

    # ── Queries ───────────────────────────────────────────────────────

    @property
    def is_running(self) -> bool:
        return self._running

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def summary(self) -> str:
        s = self.state
        return (
            f"DesktopSession: {'running' if s.running else 'stopped'} | "
            f"Screen: {s.active_screen} | "
            f"Theme: {s.current_theme} | "
            f"Uptime: {s.uptime_seconds:.0f}s"
        )
