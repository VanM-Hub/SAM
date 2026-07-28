"""DashboardRuntime — Live dashboard controller for the SAM Console.

Manages active dashboard state, refresh mode, and dirty tracking.
No business logic. No business state storage. Pure view model management.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Tuple
from datetime import datetime


class RefreshMode(Enum):
    """Dashboard refresh modes."""
    MANUAL = "manual"
    NORMAL = "normal"
    FAST = "fast"
    PAUSED = "paused"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class FilterState:
    """Current dashboard filter state (immutable)."""
    screen: str = "dashboard"
    search: str = ""
    status_filter: str = "all"
    sort_by: str = "newest"
    page: int = 1
    page_size: int = 10

    def with_page(self, page: int) -> FilterState:
        return FilterState(
            screen=self.screen, search=self.search,
            status_filter=self.status_filter, sort_by=self.sort_by,
            page=page, page_size=self.page_size,
        )

    def with_search(self, search: str) -> FilterState:
        return FilterState(
            screen=self.screen, search=search,
            status_filter=self.status_filter, sort_by=self.sort_by,
            page=1, page_size=self.page_size,
        )


@dataclass
class DashboardRuntime:
    """Live dashboard controller.

    Tracks active screen, refresh state, filter/sort state.
    Not a business object — purely view management.

    Usage:
        runtime = DashboardRuntime()
        runtime.switch_screen("missions")
        runtime.refresh()
        runtime.pause()
        runtime.resume()
    """

    active_screen: str = "dashboard"
    previous_screen: str = "dashboard"
    refresh_mode: RefreshMode = RefreshMode.MANUAL
    _dirty: bool = False
    _refresh_count: int = 0
    _refresh_callbacks: Tuple[Callable[[], None], ...] = ()
    _screen_change_callbacks: Tuple[Callable[[str, str], None], ...] = ()
    filter_state: FilterState = field(default_factory=FilterState)
    _last_refresh_time: Optional[str] = None

    def __post_init__(self) -> None:
        self._last_refresh_time = datetime.now().isoformat()

    # ── Screen management ────────────────────────────────────────────

    def switch_screen(self, screen: str) -> str:
        """Switch active screen. Returns previous screen name."""
        valid_screens = (
            "dashboard", "missions", "approvals", "timeline",
            "history", "trust", "settings", "notifications",
            "status", "log", "sessions",
        )
        if screen not in valid_screens:
            return self.active_screen

        prev = self.active_screen
        self.previous_screen = prev
        self.active_screen = screen
        self._dirty = True
        for cb in self._screen_change_callbacks:
            try:
                cb(screen, prev)
            except Exception:
                pass
        return prev

    def go_back(self) -> str:
        """Return to previous screen."""
        if self.previous_screen:
            return self.switch_screen(self.previous_screen)
        return self.active_screen

    def is_on_screen(self, screen: str) -> bool:
        """Check if a specific screen is active."""
        return self.active_screen == screen

    # ── Refresh management ───────────────────────────────────────────

    def refresh(self, source: str = "manual") -> None:
        """Trigger a dashboard refresh."""
        if self.refresh_mode == RefreshMode.PAUSED:
            return
        self._refresh_count += 1
        self._last_refresh_time = datetime.now().isoformat()
        for cb in self._refresh_callbacks:
            try:
                cb()
            except Exception:
                pass

    def pause(self) -> None:
        """Pause auto-refresh."""
        if self.refresh_mode != RefreshMode.PAUSED:
            self._last_mode = self.refresh_mode
        self.refresh_mode = RefreshMode.PAUSED

    def resume(self) -> None:
        """Resume auto-refresh to previous mode."""
        if hasattr(self, '_last_mode') and self._last_mode != RefreshMode.PAUSED:
            self.refresh_mode = self._last_mode
        else:
            self.refresh_mode = RefreshMode.NORMAL

    def set_mode(self, mode: str) -> None:
        """Set refresh mode by name."""
        for m in RefreshMode:
            if m.value == mode:
                self.refresh_mode = m
                return

    @property
    def is_paused(self) -> bool:
        return self.refresh_mode == RefreshMode.PAUSED

    @property
    def refresh_count(self) -> int:
        return self._refresh_count

    @property
    def last_refresh_time(self) -> Optional[str]:
        return self._last_refresh_time

    # ── Dirty flag ───────────────────────────────────────────────────

    @property
    def is_dirty(self) -> bool:
        return self._dirty

    def mark_clean(self) -> None:
        """Clear dirty flag after render."""
        self._dirty = False

    def mark_dirty(self) -> None:
        """Mark dashboard as needing re-render."""
        self._dirty = True

    # ── Filter / Sort ────────────────────────────────────────────────

    def set_filter(self, search: str = "", status_filter: str = "all") -> None:
        self.filter_state = self.filter_state.with_search(search)
        if status_filter != "all":
            self.filter_state = FilterState(
                screen=self.active_screen, search=search,
                status_filter=status_filter, sort_by=self.filter_state.sort_by,
                page=1, page_size=self.filter_state.page_size,
            )
        self._dirty = True

    def set_sort(self, sort_by: str) -> None:
        allowed = ("newest", "oldest", "name", "status", "priority")
        if sort_by in allowed:
            self.filter_state = FilterState(
                screen=self.active_screen, search=self.filter_state.search,
                status_filter=self.filter_state.status_filter,
                sort_by=sort_by,
                page=1, page_size=self.filter_state.page_size,
            )
            self._dirty = True

    def next_page(self) -> None:
        self.filter_state = self.filter_state.with_page(
            self.filter_state.page + 1
        )
        self._dirty = True

    def prev_page(self) -> None:
        if self.filter_state.page > 1:
            self.filter_state = self.filter_state.with_page(
                self.filter_state.page - 1
            )
            self._dirty = True

    # ── Callbacks ────────────────────────────────────────────────────

    def on_refresh(self, callback: Callable[[], None]) -> None:
        """Register refresh callback."""
        self._refresh_callbacks = self._refresh_callbacks + (callback,)

    def on_screen_change(self, callback: Callable[[str, str], None]) -> None:
        """Register screen change callback: (new_screen, prev_screen)."""
        self._screen_change_callbacks = (
            self._screen_change_callbacks + (callback,)
        )

    # ── Snapshot ─────────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "active_screen": self.active_screen,
            "previous_screen": self.previous_screen,
            "refresh_mode": str(self.refresh_mode),
            "is_paused": self.is_paused,
            "is_dirty": self.is_dirty,
            "refresh_count": self._refresh_count,
            "last_refresh_time": self._last_refresh_time,
            "filter": {
                "search": self.filter_state.search,
                "status": self.filter_state.status_filter,
                "sort": self.filter_state.sort_by,
                "page": self.filter_state.page,
                "page_size": self.filter_state.page_size,
            },
        }
