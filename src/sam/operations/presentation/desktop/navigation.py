"""DesktopNavigation — Navigation for the SAM Desktop.

Uses NavigationState and NavigationRuntime from Sprint 12/13.
Does NOT duplicate navigation state. DesktopNavigation is a thin
consumer of the existing navigation model.

Screens are defined in Sprint 12 (navigation.py):
    dashboard, missions, timeline, approvals, trust, history, settings, help
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple, List

from ..navigation import (
    NavigationState, NavigationItem, NavigationSection, Breadcrumb,
    SCREENS, SCREEN_LABELS,
    DASHBOARD, MISSIONS, APPROVALS, TIMELINE, TRUST, HISTORY, SETTINGS, HELP,
)


@dataclass(frozen=True)
class DesktopScreen:
    """A screen in the desktop navigation.

    Thin wrapper around Sprint 12 NavigationItem.
    Adds desktop-specific display hints without changing the model.
    """
    screen_id: str
    label: str
    shortcut: str = ""
    icon: str = ""  # Icon name for Qt (e.g., "folder", "clock")
    enabled: bool = True
    badge_count: int = 0


@dataclass(frozen=True)
class DesktopNavigation:
    """Desktop navigation view model.

    Consumes NavigationState from Sprint 12 NavigationRuntime.
    No duplicate state — reads from the existing model.

    This is a read-only view of navigation data for Desktop use.
    """

    # Active screen
    active_screen: str = DASHBOARD
    screen_label: str = "Dashboard"

    # Breadcrumb
    breadcrumb_trail: str = ""
    depth: int = 0

    # Screen list
    screens: Tuple[DesktopScreen, ...] = field(default_factory=lambda: (
        DesktopScreen(screen_id=DASHBOARD, label="Dashboard", shortcut="1",
                      icon="dashboard"),
        DesktopScreen(screen_id=MISSIONS, label="Missions", shortcut="2",
                      icon="playlist_check"),
        DesktopScreen(screen_id=TIMELINE, label="Timeline", shortcut="3",
                      icon="timeline"),
        DesktopScreen(screen_id=APPROVALS, label="Approvals", shortcut="4",
                      icon="check_circle"),
        DesktopScreen(screen_id=TRUST, label="Trust", shortcut="5",
                      icon="verified_user"),
        DesktopScreen(screen_id=HISTORY, label="History", shortcut="6",
                      icon="history"),
        DesktopScreen(screen_id=SETTINGS, label="Settings", shortcut="7",
                      icon="settings"),
        DesktopScreen(screen_id=HELP, label="Help", shortcut="8",
                      icon="help"),
    ))

    # ── Factory ──────────────────────────────────────────────────────

    @staticmethod
    def from_navigation_state(nav_state: NavigationState) -> DesktopNavigation:
        """Build DesktopNavigation from Sprint 12 NavigationState."""
        screens: List[DesktopScreen] = []
        for section in nav_state.sections:
            for item in section.items:
                screens.append(DesktopScreen(
                    screen_id=item.screen,
                    label=item.label,
                    shortcut=item.shortcut,
                    enabled=item.enabled,
                    badge_count=item.notification_badge,
                ))

        return DesktopNavigation(
            active_screen=nav_state.active_screen,
            screen_label=nav_state.screen_label,
            breadcrumb_trail=nav_state.breadcrumb.trail,
            depth=nav_state.breadcrumb.depth,
            screens=tuple(screens),
        )

    # ── Queries ──────────────────────────────────────────────────────

    def screen_by_id(self, screen_id: str) -> Optional[DesktopScreen]:
        """Find a screen by its identifier."""
        for s in self.screens:
            if s.screen_id == screen_id:
                return s
        return None

    def screen_by_index(self, index: int) -> Optional[DesktopScreen]:
        """Find a screen by its position (0-based)."""
        if 0 <= index < len(self.screens):
            return self.screens[index]
        return None

    @property
    def screen_count(self) -> int:
        return len(self.screens)

    @property
    def main_screens(self) -> Tuple[DesktopScreen, ...]:
        """First 4 screens (dashboard, missions, timeline, approvals)."""
        return self.screens[:4]

    @property
    def system_screens(self) -> Tuple[DesktopScreen, ...]:
        """Last 4 screens (trust, history, settings, help)."""
        return self.screens[4:]

    @property
    def navigation_summary(self) -> str:
        return (
            f"Screen: {self.screen_label} ({self.active_screen}) | "
            f"Breadcrumb: {self.depth} levels"
        )

    def is_active(self, screen_id: str) -> bool:
        """Check if a screen is currently active."""
        return self.active_screen == screen_id

    def update_badge(self, screen_id: str, count: int) -> DesktopNavigation:
        """Return a new DesktopNavigation with updated badge count."""
        new_screens: List[DesktopScreen] = []
        for s in self.screens:
            if s.screen_id == screen_id:
                new_screens.append(DesktopScreen(
                    screen_id=s.screen_id, label=s.label,
                    shortcut=s.shortcut, icon=s.icon,
                    enabled=s.enabled, badge_count=count,
                ))
            else:
                new_screens.append(s)
        return DesktopNavigation(
            active_screen=self.active_screen,
            screen_label=self.screen_label,
            breadcrumb_trail=self.breadcrumb_trail,
            depth=self.depth,
            screens=tuple(new_screens),
        )
