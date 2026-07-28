"""NavigationRuntime — Stateless runtime for Navigation Model.

Transforms NavigationState into a navigable menu system.
No business logic. No UI events. Pure navigation data management.
Does NOT import or call any domain code.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional, List, Tuple

from .navigation import (
    NavigationState, NavigationItem, NavigationSection, Breadcrumb,
    SCREENS, SCREEN_LABELS,
    DASHBOARD, MISSIONS, APPROVALS, TIMELINE, TRUST, HISTORY, SETTINGS, HELP,
)


EXIT = "exit"

SCREEN_ORDER: tuple = SCREENS + (EXIT,)


@dataclass(frozen=True)
class NavigationMenu:
    """Complete navigation menu ready for rendering."""
    active_screen: str = DASHBOARD
    sections: tuple[NavigationSection, ...] = field(default_factory=tuple)
    breadcrumb_trail: str = ""
    screen_label: str = "Dashboard"
    depth: int = 0
    exit_label: str = "Exit"

    @property
    def is_exit(self) -> bool:
        return self.active_screen == EXIT

    @property
    def total_items(self) -> int:
        return sum(s.item_count for s in self.sections)


@dataclass
class NavigationRuntime:
    """Stateless runtime that interprets NavigationState.

    Generates NavigationMenu from NavigationState.
    Validates screen transitions.
    Manages breadcrumb without side effects.
    """

    def __init__(self) -> None:
        self._state: NavigationState = NavigationState()

    @property
    def state(self) -> NavigationState:
        return self._state

    @property
    def menu(self) -> NavigationMenu:
        """Generate current NavigationMenu from NavigationState."""
        return NavigationMenu(
            active_screen=self._state.active_screen,
            sections=self._state.sections,
            breadcrumb_trail=self._state.breadcrumb.trail,
            screen_label=self._state.screen_label,
            depth=self._state.breadcrumb.depth,
        )

    # ── Screen transitions ────────────────────────────────────────────

    def navigate_to(self, screen: str) -> bool:
        """Navigate to a screen. Returns True if valid."""
        if screen not in SCREENS:
            return False
        self._state = NavigationState(
            active_screen=screen,
            breadcrumb=self._state.breadcrumb.push(screen),
            sections=self._state.sections,
        )
        return True

    def go_back(self, steps: int = 1) -> bool:
        """Go back N screens. Returns True if we moved."""
        if self._state.breadcrumb.depth == 0:
            return False
        self._state = NavigationState(
            active_screen=self._state.breadcrumb.back(steps).current or DASHBOARD,
            breadcrumb=self._state.breadcrumb.back(steps),
            sections=self._state.sections,
        )
        return True

    def go_home(self) -> None:
        """Navigate to dashboard, clearing breadcrumb."""
        self._state = NavigationState(
            active_screen=DASHBOARD,
            breadcrumb=Breadcrumb(),
            sections=self._state.sections,
        )

    def next_screen(self) -> bool:
        """Move to next screen in SCREEN_ORDER. Returns True if wrapped."""
        current_idx = SCREEN_ORDER.index(self._state.active_screen) if self._state.active_screen in SCREEN_ORDER else -1
        next_idx = (current_idx + 1) % len(SCREEN_ORDER)
        return self.navigate_to(SCREEN_ORDER[next_idx])

    def previous_screen(self) -> bool:
        """Move to previous screen in SCREEN_ORDER."""
        current_idx = SCREEN_ORDER.index(self._state.active_screen) if self._state.active_screen in SCREEN_ORDER else -1
        prev_idx = (current_idx - 1) % len(SCREEN_ORDER)
        return self.navigate_to(SCREEN_ORDER[prev_idx])

    def navigate_to_by_shortcut(self, shortcut: str) -> bool:
        """Navigate via number shortcut (1-8)."""
        mapping = {"1": DASHBOARD, "2": MISSIONS, "3": APPROVALS, "4": TIMELINE,
                    "5": TRUST, "6": HISTORY, "7": SETTINGS, "8": HELP, "9": EXIT}
        target = mapping.get(shortcut)
        if not target:
            return False
        if target == EXIT:
            self._state = NavigationState(
                active_screen=EXIT,
                breadcrumb=self._state.breadcrumb,
                sections=self._state.sections,
            )
            return True
        return self.navigate_to(target)

    # ── Queries ───────────────────────────────────────────────────────

    def is_active(self, screen: str) -> bool:
        """Check if a screen is currently active."""
        return self._state.active_screen == screen

    def is_valid(self, screen: str) -> bool:
        """Check if a screen name is valid."""
        return screen in SCREENS or screen == EXIT

    def screen_for_index(self, index: int) -> Optional[str]:
        """Get screen name at position in navigation order."""
        if 0 <= index < len(SCREEN_ORDER):
            return SCREEN_ORDER[index]
        return None

    def get_badge_count(self) -> dict:
        """Get notification badges for each screen."""
        badges: dict = {}
        for section in self._state.sections:
            for item in section.items:
                badges[item.screen] = item.notification_badge
        return badges

    # ── State updates ─────────────────────────────────────────────────

    def set_search(self, query: str) -> None:
        """Set search query without changing navigation."""
        self._state = NavigationState(
            active_screen=self._state.active_screen,
            breadcrumb=self._state.breadcrumb,
            sections=self._state.sections,
            search_query=query,
        )

    def update_badge(self, screen: str, count: int) -> None:
        """Update notification badge for a screen."""
        new_sections: list = []
        for section in self._state.sections:
            new_items = []
            for item in section.items:
                if item.screen == screen:
                    new_items.append(NavigationItem(
                        screen=item.screen, label=item.label,
                        shortcut=item.shortcut, notification_badge=count,
                    ))
                else:
                    new_items.append(item)
            new_sections.append(NavigationSection(
                title=section.title, items=tuple(new_items),
            ))
        self._state = NavigationState(
            active_screen=self._state.active_screen,
            breadcrumb=self._state.breadcrumb,
            sections=tuple(new_sections),
        )
