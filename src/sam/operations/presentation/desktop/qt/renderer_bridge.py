"""QtRendererBridge — Bridge between RendererProtocol and Qt widgets.

Consumes WidgetActions from DesktopRendererAdapter and dispatches
them to the appropriate Qt widget. No renderer changes.

Pipeline:
    RendererProtocol -> DesktopRendererAdapter -> WidgetAction -> QtRendererBridge -> QWidget
"""

from __future__ import annotations

from typing import Optional, Dict, List, Tuple, Callable

try:
    from PySide6.QtWidgets import (
        QWidget, QLabel, QTextEdit, QListWidget,
        QTreeWidget, QListWidgetItem,
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False

from ..renderer_adapter import WidgetAction, DesktopRendererAdapter, ActionQueue
from .main_window import QtMainWindow
from .docks import QtDockManager
from .navigation_tree import QtNavigationTree
from .dashboard_view import QtDashboardView
from .statusbar import QtStatusBar
from .system_tray import QtSystemTray


class QtRendererBridge:
    """Bridges DesktopRendererAdapter WidgetActions to Qt widgets.

    Reads the ActionQueue from DesktopRendererAdapter and dispatches
    each WidgetAction to the appropriate Qt widget based on widget_id.

    No renderer changes — the DesktopRendererAdapter remains unchanged.
    """

    def __init__(self, renderer_adapter: DesktopRendererAdapter):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._adapter = renderer_adapter

        # Widget registry (populated by register_widget)
        self._widgets: Dict[str, object] = {}

        # Direct text-setter targets (for docks)
        self._dock_widgets: Dict[str, object] = {}

    # ── Registration ────────────────────────────────────────────────

    def register_main_window(self, main_window: QtMainWindow) -> None:
        self._widgets["main_window"] = main_window

    def register_dock_manager(self, dock_manager: QtDockManager) -> None:
        self._widgets["docks"] = dock_manager

    def register_navigation_tree(self, nav_tree: QtNavigationTree) -> None:
        self._widgets["nav_tree"] = nav_tree

    def register_dashboard_view(self, dashboard: QtDashboardView) -> None:
        self._widgets["dashboard"] = dashboard

    def register_status_bar(self, statusbar: QtStatusBar) -> None:
        self._widgets["statusbar"] = statusbar

    def register_system_tray(self, system_tray: QtSystemTray) -> None:
        self._widgets["tray"] = system_tray

    def register_dock_widget(self, dock_id: str, widget: object) -> None:
        """Register a dock widget by dock_id for action routing."""
        self._dock_widgets[dock_id] = widget

    # ── Dispatch ────────────────────────────────────────────────────

    def process_actions(self) -> int:
        """Process all pending WidgetActions from the renderer adapter.

        Returns the number of actions processed.
        """
        actions = self._adapter.flush()
        for action in actions:
            self._dispatch(action)
        return len(actions)

    def _dispatch(self, action: WidgetAction) -> None:
        """Dispatch a single WidgetAction to the correct widget."""
        widget_id = action.widget_id

        # Dashboard
        if widget_id == "dashboard":
            dashboard = self._widgets.get("dashboard")
            if dashboard:
                dashboard.apply_action(action)

        # Status bar
        elif widget_id == "status_bar":
            sb = self._widgets.get("statusbar")
            if sb:
                sb.update_from_action(action)

        # Navigation panel
        elif widget_id == "nav_panel":
            nav = self._widgets.get("nav_tree")
            if nav and action.action == "set_content":
                pass  # Nav tree manages itself via DesktopNavigation

        # Dock widgets (mission, timeline, notifications, logs)
        elif widget_id in self._dock_widgets:
            dock_widget = self._dock_widgets[widget_id]
            if isinstance(dock_widget, QLabel):
                dock_widget.setText(action.data)
            elif isinstance(dock_widget, QTextEdit):
                if action.action == "append":
                    dock_widget.append(action.data)
                else:
                    dock_widget.setText(action.data)
            elif isinstance(dock_widget, QListWidget):
                if action.action == "append":
                    dock_widget.addItem(action.data)

        # Summary
        elif widget_id in ("summary",):
            dashboard = self._widgets.get("dashboard")
            if dashboard and action.action == "set_content":
                pass  # Dashboard processes summary via its own pipeline

    # ── Batch ───────────────────────────────────────────────────────

    def process_all(self) -> int:
        """Process all pending actions. Returns count."""
        return self.process_actions()

    def periodic_poll(self) -> None:
        """Called periodically (e.g., via QTimer) to process new actions."""
        self.process_actions()

    # ── Renderer adapter passthrough ────────────────────────────────

    @property
    def adapter(self) -> DesktopRendererAdapter:
        return self._adapter

    @property
    def pending_count(self) -> int:
        return self._adapter.action_queue.pending_count

    # ── Stats ───────────────────────────────────────────────────────

    def summary(self) -> str:
        registered = list(self._widgets.keys())
        dock_registered = list(self._dock_widgets.keys())
        return (
            f"QtRendererBridge: {len(registered)} widgets registered, "
            f"{len(dock_registered)} dock entries, "
            f"{self.pending_count} pending actions"
        )
