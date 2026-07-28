"""Navigation — Immutable navigation model for console screens.

All models are frozen. No callbacks. No UI events. No state machine.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional


DASHBOARD = "dashboard"
MISSIONS = "missions"
APPROVALS = "approvals"
TIMELINE = "timeline"
TRUST = "trust"
HISTORY = "history"
SETTINGS = "settings"
HELP = "help"

SCREENS = (DASHBOARD, MISSIONS, APPROVALS, TIMELINE, TRUST, HISTORY, SETTINGS, HELP)

SCREEN_LABELS = {
    DASHBOARD: "Dashboard",
    MISSIONS: "Missions",
    APPROVALS: "Approvals",
    TIMELINE: "Timeline",
    TRUST: "Trust",
    HISTORY: "History",
    SETTINGS: "Settings",
    HELP: "Help",
}


@dataclass(frozen=True)
class NavigationItem:
    """A single navigation item."""
    screen: str = DASHBOARD
    label: str = "Dashboard"
    shortcut: str = ""
    notification_badge: int = 0
    enabled: bool = True


@dataclass(frozen=True)
class NavigationSection:
    """A group of navigation items."""
    title: str = "Main"
    items: tuple[NavigationItem, ...] = field(default_factory=tuple)

    @property
    def item_count(self) -> int:
        return len(self.items)


@dataclass(frozen=True)
class Breadcrumb:
    """Breadcrumb trail — tracks navigation history."""
    screens: tuple[str, ...] = field(default_factory=tuple)

    @property
    def current(self) -> Optional[str]:
        if self.screens:
            return self.screens[-1]
        return None

    @property
    def trail(self) -> str:
        return " > ".join(SCREEN_LABELS.get(s, s) for s in self.screens)

    @property
    def depth(self) -> int:
        return len(self.screens)

    def push(self, screen: str) -> Breadcrumb:
        return Breadcrumb(screens=self.screens + (screen,))

    def pop(self) -> Breadcrumb:
        if not self.screens:
            return self
        return Breadcrumb(screens=self.screens[:-1])

    def back(self, steps: int = 1) -> Breadcrumb:
        if steps >= len(self.screens):
            return Breadcrumb(screens=())
        return Breadcrumb(screens=self.screens[:-steps])


@dataclass(frozen=True)
class NavigationState:
    """Complete navigation state — pure data. No listeners. No callbacks."""
    active_screen: str = DASHBOARD
    breadcrumb: Breadcrumb = field(default_factory=Breadcrumb)
    sections: tuple[NavigationSection, ...] = field(default_factory=lambda: (
        NavigationSection(
            title="Main",
            items=(
                NavigationItem(screen=DASHBOARD, label="Dashboard", shortcut="1"),
                NavigationItem(screen=MISSIONS, label="Missions", shortcut="2"),
                NavigationItem(screen=APPROVALS, label="Approvals", shortcut="3"),
                NavigationItem(screen=TIMELINE, label="Timeline", shortcut="4"),
            ),
        ),
        NavigationSection(
            title="System",
            items=(
                NavigationItem(screen=TRUST, label="Trust", shortcut="5"),
                NavigationItem(screen=HISTORY, label="History", shortcut="6"),
                NavigationItem(screen=SETTINGS, label="Settings", shortcut="7"),
                NavigationItem(screen=HELP, label="Help", shortcut="8"),
            ),
        ),
    ))
    search_query: str = ""

    @property
    def screen_label(self) -> str:
        return SCREEN_LABELS.get(self.active_screen, self.active_screen)

    @property
    def is_dashboard(self) -> bool:
        return self.active_screen == DASHBOARD

    @property
    def is_missions(self) -> bool:
        return self.active_screen == MISSIONS

    @property
    def is_approvals(self) -> bool:
        return self.active_screen == APPROVALS
