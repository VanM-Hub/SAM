"""DesktopMainWindow — Window model for the SAM Desktop.

Defines the data model for a desktop window: menu bar, toolbar,
navigation panel, content area, status bar, notification area, and
system tray. All are model/data only — no Qt widget implementations.

No business logic. No rendering.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple, List


@dataclass(frozen=True)
class MenuItem:
    """A menu entry in the desktop menu bar.

    Represents a single action or submenu. No callbacks.
    """
    label: str
    shortcut: str = ""  # e.g., "Ctrl+Q"
    icon: str = ""       # Icon name for Qt
    enabled: bool = True
    separator_before: bool = False
    children: Tuple[MenuItem, ...] = ()

    @property
    def has_children(self) -> bool:
        return len(self.children) > 0


@dataclass(frozen=True)
class ToolbarItem:
    """A toolbar entry in the desktop toolbar.

    Represents an action button. No callbacks.
    """
    label: str
    icon: str = ""
    tooltip: str = ""
    enabled: bool = True
    separator_before: bool = False


@dataclass(frozen=True)
class NotificationArea:
    """System tray / notification area data model.

    No callbacks. No Qt references.
    """
    visible: bool = True
    icon: str = "SAM"        # Icon name
    tooltip: str = "SAM Desktop"
    unread_count: int = 0
    critical_count: int = 0


@dataclass(frozen=True)
class DesktopWindow:
    """Complete window model for the SAM Desktop.

    Immutable model of the window structure.
    No Qt widget references. No business logic.
    """

    # Window state
    title: str = "SAM Desktop"
    width: int = 1280
    height: int = 800
    x: int = -1   # -1 = center
    y: int = -1   # -1 = center
    maximized: bool = False
    minimized: bool = False
    fullscreen: bool = False

    # Menu bar
    menu_items: Tuple[MenuItem, ...] = field(default_factory=lambda: (
        MenuItem(label="File", children=(
            MenuItem(label="New Session", shortcut="Ctrl+N"),
            MenuItem(label="Open...", shortcut="Ctrl+O"),
            MenuItem(label="", shortcut="", separator_before=True),
            MenuItem(label="Exit", shortcut="Ctrl+Q"),
        )),
        MenuItem(label="View", children=(
            MenuItem(label="Dashboard", shortcut="Ctrl+1"),
            MenuItem(label="Missions", shortcut="Ctrl+2"),
            MenuItem(label="Timeline", shortcut="Ctrl+3"),
            MenuItem(label="Approvals", shortcut="Ctrl+4"),
            MenuItem(label="", shortcut="", separator_before=True),
            MenuItem(label="Toggle Log Panel", shortcut="Ctrl+L"),
            MenuItem(label="Toggle Nav Panel", shortcut="Ctrl+Shift+N"),
        )),
        MenuItem(label="Tools", children=(
            MenuItem(label="Refresh", shortcut="F5"),
            MenuItem(label="Force Refresh", shortcut="Ctrl+F5"),
            MenuItem(label="", shortcut="", separator_before=True),
            MenuItem(label="Settings...", shortcut="Ctrl+,"),
        )),
        MenuItem(label="Help", children=(
            MenuItem(label="Help Contents", shortcut="F1"),
            MenuItem(label="About SAM", shortcut=""),
        )),
    ))

    # Toolbar
    toolbar_items: Tuple[ToolbarItem, ...] = field(default_factory=lambda: (
        ToolbarItem(label="Dashboard", icon="dashboard", tooltip="Go to Dashboard"),
        ToolbarItem(label="Refresh", icon="refresh", tooltip="Refresh (F5)"),
        ToolbarItem(label="", tooltip="", separator_before=True),
        ToolbarItem(label="Settings", icon="settings", tooltip="Settings"),
    ))

    # Status bar content
    status_text: str = "Ready"
    connection_status: str = "Connected"
    mission_count: str = "0 missions"

    # Notification area
    notification_area: NotificationArea = field(default_factory=NotificationArea)

    # ── Factory helpers ──────────────────────────────────────────────

    @staticmethod
    def default() -> DesktopWindow:
        return DesktopWindow()

    @staticmethod
    def minimal() -> DesktopWindow:
        """Minimal window without toolbar."""
        return DesktopWindow(
            title="SAM Desktop",
            width=1024, height=600,
            toolbar_items=(),
        )

    # ── Queries ──────────────────────────────────────────────────────

    def with_status(self, text: str) -> DesktopWindow:
        """Return a new window with updated status text."""
        return DesktopWindow(
            title=self.title, width=self.width, height=self.height,
            x=self.x, y=self.y,
            maximized=self.maximized, minimized=self.minimized,
            fullscreen=self.fullscreen,
            menu_items=self.menu_items,
            toolbar_items=self.toolbar_items,
            status_text=text,
            connection_status=self.connection_status,
            mission_count=self.mission_count,
            notification_area=self.notification_area,
        )

    def with_notification(self, unread: int, critical: int = 0) -> DesktopWindow:
        """Return a new window with updated notification counts."""
        return DesktopWindow(
            title=self.title, width=self.width, height=self.height,
            x=self.x, y=self.y,
            maximized=self.maximized, minimized=self.minimized,
            fullscreen=self.fullscreen,
            menu_items=self.menu_items,
            toolbar_items=self.toolbar_items,
            status_text=self.status_text,
            connection_status=self.connection_status,
            mission_count=self.mission_count,
            notification_area=NotificationArea(
                visible=self.notification_area.visible,
                icon=self.notification_area.icon,
                tooltip=self.notification_area.tooltip,
                unread_count=unread,
                critical_count=critical,
            ),
        )
