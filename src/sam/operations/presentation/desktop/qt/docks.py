"""QtDockManager — Dock widgets for the SAM Desktop.

QDockWidget panels: Navigation, Mission, Timeline, Notifications, Logs.
All data consumed from RendererProtocol bridge. No business logic.
"""

from __future__ import annotations

from typing import Optional, Dict, List, Tuple

try:
    from PySide6.QtWidgets import (
        QDockWidget, QWidget, QVBoxLayout, QLabel,
        QTreeWidget, QTextEdit, QListWidget,
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QDockWidget = object

from .main_window import QtMainWindow


# ── Dock Panel ─────────────────────────────────────────────────────────

class QtDockPanel:
    """A single dock panel (QDockWidget wrapper).

    Each panel has: id, title, content widget, visibility state.
    """

    def __init__(self, dock_id: str, title: str, area: str = "left"):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._id = dock_id
        self._title = title
        self._area = area
        self._qdock: Optional[QDockWidget] = None
        self._content_widget: Optional[QWidget] = None

        # Dock areas
        self._area_map = {
            "left": Qt.DockWidgetArea.LeftDockWidgetArea,
            "right": Qt.DockWidgetArea.RightDockWidgetArea,
            "top": Qt.DockWidgetArea.TopDockWidgetArea,
            "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
        }

    def build(self) -> QDockWidget:
        """Build the QDockWidget."""
        self._qdock = QDockWidget(self._title)
        self._qdock.setObjectName(self._id)
        self._qdock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )

        # Default content — will be replaced by specific widgets
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)
        self._qdock.setWidget(container)
        self._content_widget = container

        return self._qdock

    def set_widget(self, widget: QWidget) -> None:
        """Replace the dock panel content widget."""
        if self._qdock:
            self._qdock.setWidget(widget)
            self._content_widget = widget

    def set_title(self, title: str) -> None:
        if self._qdock:
            self._qdock.setWindowTitle(title)

    def show(self) -> None:
        if self._qdock:
            self._qdock.show()

    def hide(self) -> None:
        if self._qdock:
            self._qdock.hide()

    @property
    def dock_id(self) -> str:
        return self._id

    @property
    def qdock(self) -> Optional[QDockWidget]:
        return self._qdock

    @property
    def title(self) -> str:
        return self._title

    @property
    def dock_area(self) -> int:
        return self._area_map.get(self._area, Qt.DockWidgetArea.LeftDockWidgetArea)


# ── Dock Manager ───────────────────────────────────────────────────────

class QtDockManager:
    """Manages all dock panels for the SAM Desktop.

    Creates and registers dock widgets from configuration.
    Supports: Navigation, Mission, Timeline, Notifications, Logs.
    """

    DOCK_IDS = ["navigation", "mission", "timeline", "notifications", "logs"]

    def __init__(self, main_window: QtMainWindow):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._main = main_window
        self._docks: Dict[str, QtDockPanel] = {}

        # Content widgets (set by specific builders)
        self._widgets: Dict[str, QWidget] = {}

    def build_all(self) -> List[QDockWidget]:
        """Build all standard dock panels. Returns list of QDockWidget."""
        dock_config = {
            "navigation":    ("Navigation",    "left"),
            "mission":       ("Missions",      "left"),
            "timeline":      ("Timeline",      "right"),
            "notifications": ("Notifications", "right"),
            "logs":          ("Logs",          "bottom"),
        }

        built = []
        for dock_id, (title, area) in dock_config.items():
            panel = QtDockPanel(dock_id, title, area)
            qdock = panel.build()

            qmain = self._main.qmain
            if qmain:
                qmain.addDockWidget(panel.dock_area, qdock)
                # Replace default content with appropriate widget
                widget = self._create_default_widget(dock_id)
                if widget:
                    panel.set_widget(widget)
                    self._widgets[dock_id] = widget

            self._docks[dock_id] = panel
            built.append(qdock)

        return built

    def _create_default_widget(self, dock_id: str) -> Optional[QWidget]:
        """Create a default content widget for a dock panel."""
        if dock_id == "navigation":
            tree = QTreeWidget()
            tree.setHeaderLabel("Navigation")
            return tree
        elif dock_id == "logs":
            logs = QTextEdit()
            logs.setReadOnly(True)
            return logs
        elif dock_id in ("notifications",):
            notif_list = QListWidget()
            return notif_list
        else:
            # Default label
            label = QLabel(f"<b>{dock_id.title()}</b>")
            label.setAlignment(Qt.AlignCenter)
            return label

    def get_widget(self, dock_id: str) -> Optional[QWidget]:
        return self._widgets.get(dock_id)

    def get_panel(self, dock_id: str) -> Optional[QtDockPanel]:
        return self._docks.get(dock_id)

    def get_qlabel_widget(self, dock_id: str) -> Optional["QLabel"]:
        """Get QLabel widget from a dock (for text-based docks)."""
        widget = self._widgets.get(dock_id)
        if isinstance(widget, QLabel):
            return widget
        return None

    def get_qtextedit_widget(self, dock_id: str) -> Optional["QTextEdit"]:
        widget = self._widgets.get(dock_id)
        if isinstance(widget, QTextEdit):
            return widget
        return None

    def get_qlist_widget(self, dock_id: str) -> Optional["QListWidget"]:
        widget = self._widgets.get(dock_id)
        if isinstance(widget, QListWidget):
            return widget
        return None

    def get_qtree_widget(self, dock_id: str) -> Optional["QTreeWidget"]:
        widget = self._widgets.get(dock_id)
        if isinstance(widget, QTreeWidget):
            return widget
        return None

    @property
    def panels(self) -> Dict[str, QtDockPanel]:
        return self._docks

    def summary(self) -> str:
        active = [k for k, v in self._docks.items() if v.qdock and v.qdock.isVisible()]
        return f"DockManager: {len(self._docks)} docks, {len(active)} visible"

    # ── Layout state ──────────────────────────────────────────────────

    def apply_layout(self, layout) -> None:
        """Apply a DesktopLayout model to dock visibility and state.

        Args:
            layout: DesktopLayout from Sprint 16 (OP-205).
        """
        if not layout:
            return

        from ..layout import DesktopLayout
        if not isinstance(layout, DesktopLayout):
            return

        # Left panel → navigation dock visibility
        nav_panel = self.get_panel("navigation")
        if nav_panel:
            region = layout.left_panel
            if region.collapsed:
                nav_panel.hide()
            else:
                nav_panel.show()

        # Right panel → timeline/notifications visibility
        right = self.get_panel("timeline")
        if right:
            region = layout.right_panel
            if region.collapsed:
                right.hide()
            else:
                right.show()

        # Bottom panel → logs visibility
        logs = self.get_panel("logs")
        if logs:
            region = layout.bottom_panel
            if region.collapsed:
                logs.hide()
            else:
                logs.show()
