"""QtMainWindow — QMainWindow for the SAM Desktop.

Title, icon, menu bar, tool bar, status bar, central widget.
All data sourced from DesktopWindow model (Sprint 16, OP-203).
No business logic. No domain imports.
"""

from __future__ import annotations

from typing import Optional, Dict, Callable

try:
    from PySide6.QtWidgets import (
        QMainWindow, QWidget, QVBoxLayout, QMenuBar,
        QToolBar, QStatusBar, QLabel,
    )
    from PySide6.QtCore import Qt, QSize
    from PySide6.QtGui import QAction, QIcon, QKeySequence
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QMainWindow = object

from .application import QtApplication
from ..main_window import DesktopWindow, MenuItem, ToolbarItem
from ..layout import DesktopLayout


class QtMainWindow:
    """SAM Desktop main window (QMainWindow wrapper).

    Consumes DesktopWindow model for structure.
    All actions are routed through the renderer bridge.
    """

    def __init__(self, qt_app: QtApplication, desktop_window: Optional[DesktopWindow] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._qt_app = qt_app
        self._window = desktop_window or DesktopWindow.default()
        self._layout = DesktopLayout()
        self._qmain: Optional[QMainWindow] = None
        self._central_widget: Optional[QWidget] = None
        self._action_handlers: Dict[str, Callable] = {}

        # Registered dock widgets (populated by QtDockManager)
        self._docks: Dict[str, object] = {}

    # ── Build ─────────────────────────────────────────────────────────

    def build(self) -> QMainWindow:
        """Build the full QMainWindow from DesktopWindow model."""
        qmain = QMainWindow()

        # Window geometry from model
        qmain.setWindowTitle(self._window.title)
        if self._window.x >= 0 and self._window.y >= 0:
            qmain.move(self._window.x, self._window.y)
        qmain.resize(self._window.width, self._window.height)

        if self._window.maximized:
            qmain.showMaximized()

        # Central widget
        central = QWidget()
        central.setLayout(QVBoxLayout())
        qmain.setCentralWidget(central)
        self._central_widget = central

        # Build sub-components
        self._build_menu_bar(qmain)
        self._build_tool_bar(qmain)
        self._build_status_bar(qmain)

        qmain.show()
        self._qmain = qmain
        return qmain

    def _build_menu_bar(self, qmain: QMainWindow) -> None:
        """Build menu bar from DesktopWindow menu items."""
        menu_bar = qmain.menuBar()
        if not menu_bar:
            return
        menu_bar.clear()

        for item in self._window.menu_items:
            if not item.label:
                continue
            menu = menu_bar.addMenu(item.label)
            for child in item.children:
                self._add_menu_action(menu, child)

    def _add_menu_action(self, menu, item: MenuItem) -> None:
        """Add a single menu action or separator."""
        if item.separator_before or not item.label:
            menu.addSeparator()
            if not item.label:
                return
        action = QAction(item.label, self._qmain)
        if item.shortcut:
            action.setShortcut(QKeySequence(item.shortcut))
        if item.icon:
            try:
                action.setIcon(QIcon(item.icon))
            except Exception:
                pass
        action.setEnabled(item.enabled)
        # Wire handler
        handler = self._action_handlers.get(item.label)
        if handler:
            action.triggered.connect(handler)
        menu.addAction(action)

    def _build_tool_bar(self, qmain: QMainWindow) -> None:
        """Build toolbar from DesktopWindow toolbar items."""
        if not self._window.toolbar_items:
            return
        toolbar = QToolBar("Main Toolbar")
        toolbar.setMovable(False)

        for titem in self._window.toolbar_items:
            if titem.separator_before or not titem.label:
                toolbar.addSeparator()
                if not titem.label:
                    continue
            action = QAction(titem.label, self._qmain)
            if titem.tooltip:
                action.setToolTip(titem.tooltip)
            action.setEnabled(titem.enabled)
            handler = self._action_handlers.get(titem.label)
            if handler:
                action.triggered.connect(handler)
            toolbar.addAction(action)

        qmain.addToolBar(toolbar)

    def _build_status_bar(self, qmain: QMainWindow) -> None:
        """Build status bar from DesktopWindow status."""
        status_bar = qmain.statusBar()
        if status_bar:
            status_bar.showMessage(self._window.status_text)

    # ── Properties ────────────────────────────────────────────────────

    @property
    def qmain(self) -> Optional[QMainWindow]:
        return self._qmain

    @property
    def central_widget(self) -> Optional[QWidget]:
        return self._central_widget

    @property
    def window_model(self) -> DesktopWindow:
        return self._window

    @property
    def window_title(self) -> str:
        return self._window.title

    @window_title.setter
    def window_title(self, title: str) -> None:
        if self._qmain:
            self._qmain.setWindowTitle(title)

    # ── Actions ───────────────────────────────────────────────────────

    def on_action(self, label: str, handler: Callable) -> None:
        """Register a handler for a menu/toolbar action."""
        self._action_handlers[label] = handler

    def set_status(self, text: str) -> None:
        """Update status bar text."""
        if self._qmain:
            sb = self._qmain.statusBar()
            if sb:
                sb.showMessage(text)

    def set_central(self, widget: QWidget) -> None:
        """Replace the central widget."""
        if self._qmain:
            self._qmain.setCentralWidget(widget)
            self._central_widget = widget

    def add_dock(self, dock_id: str, dock_widget) -> None:
        """Register a dock widget."""
        self._docks[dock_id] = dock_widget

    # ── Theme ─────────────────────────────────────────────────────────

    def apply_theme(self, stylesheet: str) -> None:
        """Apply Qt stylesheet to the main window."""
        if self._qmain and stylesheet:
            self._qmain.setStyleSheet(stylesheet)

    # ── Lifetime ──────────────────────────────────────────────────────

    def close(self) -> None:
        """Close the main window."""
        if self._qmain:
            self._qmain.close()

    def show(self) -> None:
        if self._qmain:
            self._qmain.show()

    def hide(self) -> None:
        if self._qmain:
            self._qmain.hide()
