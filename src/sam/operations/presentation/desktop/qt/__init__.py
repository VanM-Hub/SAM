"""desktop.qt — Qt widget implementations for the SAM Desktop.

All widgets consume data via RendererProtocol bridge.
No domain imports. No business logic. No Conversation API bypass.

This module is Qt-dependent (PySide6).
"""

from __future__ import annotations

from .application import QtApplication
from .main_window import QtMainWindow
from .docks import QtDockManager, QtDockPanel
from .navigation_tree import QtNavigationTree
from .dashboard_view import QtDashboardView
from .statusbar import QtStatusBar
from .system_tray import QtSystemTray
from .renderer_bridge import QtRendererBridge

__all__ = [
    "QtApplication",
    "QtMainWindow",
    "QtDockManager", "QtDockPanel",
    "QtNavigationTree",
    "QtDashboardView",
    "QtStatusBar",
    "QtSystemTray",
    "QtRendererBridge",
]
