"""desktop.qt — Qt widget implementations for the SAM Desktop.

All widgets consume data via RendererProtocol bridge.
No domain imports. No business logic. No Conversation API bypass.

This module is Qt-dependent (PySide6).
"""

from __future__ import annotations

from .application import QtApplication
from .main_window import QtMainWindow

# Sprint 17
from .docks import QtDockManager as QtDockManagerV17
from .navigation_tree import QtNavigationTree
from .dashboard_view import QtDashboardView
from .statusbar import QtStatusBar
from .system_tray import QtSystemTray
from .renderer_bridge import QtRendererBridge

# Sprint 18
from .workspace import WorkspaceManager, WorkspaceState, WorkspaceRegion
from .dock_manager import QtDockManager, DockPanel
from .mission_widget import MissionTableWidget
from .timeline_widget import TimelineWidget
from .dashboard_widget import DashboardWidget
from .notification_panel import NotificationPanel
from .log_viewer_widget import LogViewerWidget
from .command_palette import CommandPalette

__all__ = [
    # App
    "QtApplication",
    "QtMainWindow",

    # Sprint 17
    "QtDockManagerV17",
    "QtNavigationTree",
    "QtDashboardView",
    "QtStatusBar",
    "QtSystemTray",
    "QtRendererBridge",

    # Sprint 18 — Workspace
    "WorkspaceManager", "WorkspaceState", "WorkspaceRegion",

    # Sprint 18 — Dock Manager
    "QtDockManager", "DockPanel",

    # Sprint 18 — Widgets
    "MissionTableWidget",
    "TimelineWidget",
    "DashboardWidget",
    "NotificationPanel",
    "LogViewerWidget",
    "CommandPalette",
]
