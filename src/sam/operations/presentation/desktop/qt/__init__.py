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

# Sprint 19 — Operational Workbench
from .export_center import ExportCenter, ExportPreviewDialog
from .workspace_profiles import (
    WorkspaceProfiles, WorkspaceProfile, ProfileRegion,
    ProfileSelectorDialog,
)
from .dock_persistence import DockPersistence
from .embedded_terminal import EmbeddedTerminal
from .toolbar_actions import (
    ToolbarActions, ToolbarActionDef, ActionId,
)
from .timeline_explorer import TimelineExplorer
from .mission_inspector import MissionInspector
from .approval_dialog import ApprovalDialog, ApprovalCenter
from .operator_prod import (
    ProductivityManager, ProductivityPanel,
    RecentCommand, FavoriteCommand, Bookmark,
)

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

    # Sprint 19 — Export
    "ExportCenter", "ExportPreviewDialog",

    # Sprint 19 — Profiles
    "WorkspaceProfiles", "WorkspaceProfile", "ProfileRegion",
    "ProfileSelectorDialog",

    # Sprint 19 — Persistence
    "DockPersistence",

    # Sprint 19 — Terminal
    "EmbeddedTerminal",

    # Sprint 19 — Toolbar
    "ToolbarActions", "ToolbarActionDef", "ActionId",

    # Sprint 19 — Timeline
    "TimelineExplorer",

    # Sprint 19 — Mission Inspector
    "MissionInspector",

    # Sprint 19 — Approval
    "ApprovalDialog", "ApprovalCenter",

    # Sprint 19 — Productivity
    "ProductivityManager", "ProductivityPanel",
    "RecentCommand", "FavoriteCommand", "Bookmark",
]
