"""LiveRefresh — Synchronous refresh coordinator for Console.

Wraps RefreshController from Sprint 12 with a sync polling loop.
No threads. No async. No timers.
Supports manual, interval, and event-based refresh modes.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Optional, List, Tuple
from datetime import datetime

from .refresh import RefreshController, RefreshMode, RefreshState


DEFAULT_INTERVAL_SECONDS = 10


@dataclass
class RefreshCallback:
    """A registered refresh callback."""
    name: str
    callback: Callable
    section: str = "full"


class LiveRefresh:
    """Synchronous refresh coordinator.

    Usage:
        refresh = LiveRefresh()
        refresh.register("dashboard", render_fn)
        refresh.register("notifications", notify_fn, "notification")

        if refresh.should_refresh(seconds_since_last=5):
            refresh.execute()

    Thread-safe: single-threaded. No async. No threading.
    """

    def __init__(self, mode: RefreshMode = RefreshMode.TEN_SECOND) -> None:
        self._controller = RefreshController()
        self._controller.set_mode(mode)
        self._callbacks: List[RefreshCallback] = []
        self._last_interval_check: float = 0.0

    @property
    def state(self) -> RefreshState:
        return self._controller.state

    # ── Callback management ───────────────────────────────────────────

    def register(self, name: str, callback: Callable,
                 section: str = "full") -> None:
        """Register a refresh callback."""
        self._callbacks.append(RefreshCallback(name=name, callback=callback,
                                                section=section))

    def unregister(self, name: str) -> bool:
        """Remove a registered callback. Returns True if found."""
        for i, cb in enumerate(self._callbacks):
            if cb.name == name:
                self._callbacks.pop(i)
                return True
        return False

    def clear_callbacks(self) -> None:
        """Remove all callbacks."""
        self._callbacks.clear()

    # ── Mode management ───────────────────────────────────────────────

    @property
    def mode(self) -> RefreshMode:
        return self._controller.state.mode

    def set_mode(self, mode: RefreshMode) -> None:
        """Change refresh mode."""
        self._controller.set_mode(mode)

    def pause(self) -> None:
        """Pause all refresh."""
        self._controller.pause()

    def resume(self) -> None:
        """Resume refresh."""
        self._controller.resume()

    @property
    def is_paused(self) -> bool:
        return self._controller.state.is_paused

    # ── Dirty marking ─────────────────────────────────────────────────

    def mark_dirty(self, *sections: str) -> None:
        """Mark sections as needing refresh."""
        self._controller.mark_dirty(*sections)

    # ── Refresh decision ──────────────────────────────────────────────

    def should_refresh(self, seconds_since_last: float) -> bool:
        """Check if a refresh is needed based on mode and timing.

        Args:
            seconds_since_last: Time since last full refresh in seconds.

        Returns:
            True if a refresh should be performed.
        """
        if self._controller.needs_refresh():
            return True

        if self.is_paused:
            return False

        interval = self._controller.state.interval_seconds
        if interval <= 0:
            return False  # Manual or event only

        return seconds_since_last >= interval

    # ── Execution ─────────────────────────────────────────────────────

    def execute(self, sections: Optional[Tuple[str, ...]] = None) -> int:
        """Execute all registered callbacks.

        Args:
            sections: If provided, only callbacks matching these sections
                     are executed. If None, all are executed (full refresh).

        Returns:
            Number of callbacks executed.
        """
        self._controller.mark_dirty()
        count = 0

        for cb in self._callbacks:
            if sections and cb.section not in sections and cb.section != "full":
                continue
            try:
                cb.callback()
                count += 1
            except Exception:
                pass  # Callback errors are non-fatal

        if sections:
            self._controller.partial_refresh(*sections)
        else:
            self._controller.full_refresh()

        return count

    def execute_all(self) -> int:
        """Execute all callbacks (full refresh)."""
        return self.execute()

    def execute_section(self, section: str) -> int:
        """Execute callbacks for a specific section."""
        return self.execute(sections=(section,))

    # ── Event-based refresh ───────────────────────────────────────────

    def on_notification(self) -> None:
        """Mark notification section dirty."""
        self.mark_dirty("notification")

    def on_mission_update(self) -> None:
        """Mark mission section dirty."""
        self.mark_dirty("mission")

    def on_approval(self) -> None:
        """Mark approval section dirty."""
        self.mark_dirty("approval")

    def on_timeline_event(self) -> None:
        """Mark timeline section dirty."""
        self.mark_dirty("timeline")

    def on_trust_change(self) -> None:
        """Mark trust section dirty."""
        self.mark_dirty("trust")

    @property
    def dirty_sections(self) -> Tuple[str, ...]:
        return self._controller.state.dirty_sections

    @property
    def is_dirty(self) -> bool:
        return self._controller.state.is_dirty

    # ── Inspection ────────────────────────────────────────────────────

    def summary(self) -> str:
        """Get a human-readable summary of refresh state."""
        st = self.state
        mode_name = st.mode.value
        paused = " (paused)" if st.is_paused else ""
        dirty = f", {len(st.dirty_sections)} dirty" if st.is_dirty else ""
        cbs = len(self._callbacks)
        return f"Refresh: {mode_name}{paused}{dirty}, {cbs} callbacks"
