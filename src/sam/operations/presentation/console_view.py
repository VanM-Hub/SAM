"""ConsoleView — Immutable ViewModel for console output.

Pure dataclass. No render(), no print(), no Rich, no Textual.
Fully serializable. Ready for any renderer (Console/Desktop/Web).
"""

from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime


@dataclass(frozen=True)
class HeaderView:
    """Top section of the console view."""
    title: str = "SAM"
    subtitle: str = ""
    status: str = "unknown"  # "running" | "degraded" | "healthy"
    mode: str = "auto"  # "auto" | "manual" | "sleep"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class StatusBarView:
    """Bottom status bar."""
    mission_count: int = 0
    pending_approvals: int = 0
    trust_grade: str = ""
    health_status: str = ""
    last_event: str = ""
    uptime: str = ""


@dataclass(frozen=True)
class SidebarView:
    """Left sidebar — navigation and quick info."""
    active_screen: str = "dashboard"
    available_screens: tuple[str, ...] = (
        "dashboard", "missions", "approvals", "timeline",
        "trust", "history", "settings", "help",
    )
    notification_count: int = 0
    critical_alerts: int = 0
    current_mission: str = ""


@dataclass(frozen=True)
class BodyView:
    """Main content area — holds widget data."""
    content_type: str = "dashboard"  # "dashboard" | "detail" | "empty"
    title: str = ""
    summary: str = ""
    items: tuple[str, ...] = field(default_factory=tuple)
    columns: tuple[str, ...] = field(default_factory=tuple)
    rows: tuple[tuple[str, ...], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class FooterView:
    """Footer — shortcuts and hints."""
    hints: tuple[str, ...] = field(default_factory=lambda: (
        "Tab: nav", "Enter: select", "R: refresh", "Q: quit",
    ))
    version: str = ""
    mode: str = ""


@dataclass(frozen=True)
class ConsoleView:
    """Complete view model for a full console screen."""
    header: HeaderView = field(default_factory=HeaderView)
    sidebar: SidebarView = field(default_factory=SidebarView)
    body: BodyView = field(default_factory=BodyView)
    status_bar: StatusBarView = field(default_factory=StatusBarView)
    footer: FooterView = field(default_factory=FooterView)

    @property
    def section_count(self) -> int:
        return 5
