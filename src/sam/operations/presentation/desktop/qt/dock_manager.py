"""QtDockManager — Bridge between DesktopLayout and QDockWidget.

Separated from docks.py (Sprint 17) into its own module.
Handles: create, attach, detach, visibility, save/restore state.
Bridge between DesktopLayout (Sprint 16 OP-205) and Qt.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

try:
    from PySide6.QtWidgets import (
        QDockWidget, QWidget, QTabWidget, QMainWindow,
    )
    from PySide6.QtCore import Qt
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QDockWidget = object
    QMainWindow = object


class DockPanel:
    """A single dock panel — wraps QDockWidget with metadata."""

    def __init__(self, dock_id: str, title: str, area: str = "left"):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._id = dock_id
        self._title = title
        self._area_str = area
        self._qdock: Optional[QDockWidget] = None
        self._content: Optional[QWidget] = None

    def build(self, parent: QMainWindow) -> QDockWidget:
        """Build and attach the QDockWidget to a main window."""
        area_map = {
            "left": Qt.DockWidgetArea.LeftDockWidgetArea,
            "right": Qt.DockWidgetArea.RightDockWidgetArea,
            "top": Qt.DockWidgetArea.TopDockWidgetArea,
            "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
        }

        self._qdock = QDockWidget(self._title)
        self._qdock.setObjectName(self._id)
        self._qdock.setAllowedAreas(
            Qt.DockWidgetArea.LeftDockWidgetArea
            | Qt.DockWidgetArea.RightDockWidgetArea
        )

        container = QWidget()
        from PySide6.QtWidgets import QVBoxLayout
        container.setLayout(QVBoxLayout())
        self._qdock.setWidget(container)
        self._content = container

        parent.addDockWidget(
            area_map.get(self._area_str, Qt.DockWidgetArea.LeftDockWidgetArea),
            self._qdock,
        )
        return self._qdock

    def set_widget(self, widget: QWidget) -> None:
        if self._qdock:
            self._qdock.setWidget(widget)
            self._content = widget

    def attach_to(self, parent: QMainWindow, area: str = "left") -> None:
        """Attach dock to a main window."""
        if not self._qdock:
            return
        area_map = {
            "left": Qt.DockWidgetArea.LeftDockWidgetArea,
            "right": Qt.DockWidgetArea.RightDockWidgetArea,
            "top": Qt.DockWidgetArea.TopDockWidgetArea,
            "bottom": Qt.DockWidgetArea.BottomDockWidgetArea,
        }
        parent.addDockWidget(area_map.get(area, Qt.DockWidgetArea.LeftDockWidgetArea),
                             self._qdock)

    def detach(self) -> None:
        """Detach dock from parent (set floating)."""
        if self._qdock:
            self._qdock.setFloating(True)

    def show(self) -> None:
        if self._qdock:
            self._qdock.show()

    def hide(self) -> None:
        if self._qdock:
            self._qdock.hide()

    def set_visible(self, visible: bool) -> None:
        if visible:
            self.show()
        else:
            self.hide()

    def set_title(self, title: str) -> None:
        if self._qdock:
            self._qdock.setWindowTitle(title)

    @property
    def qdock(self) -> Optional[QDockWidget]:
        return self._qdock

    @property
    def content(self) -> Optional[QWidget]:
        return self._content

    @property
    def dock_id(self) -> str:
        return self._id

    @property
    def is_visible(self) -> Optional[bool]:
        if self._qdock:
            return self._qdock.isVisible()
        return None

    @property
    def is_floating(self) -> Optional[bool]:
        if self._qdock:
            return self._qdock.isFloating()
        return None


class QtDockManager:
    """Bridge between DesktopLayout model and QDockWidget widgets.

    - create: build docks from configuration
    - attach: attach docks to a QMainWindow
    - detach: detach docks
    - visibility: show/hide/toggle
    - save/restore: state persistence
    - apply_layout: consume DesktopLayout model
    """

    DEFAULT_DOCKS = {
        "navigation":    ("Navigation",    "left"),
        "mission":       ("Missions",      "left"),
        "timeline":      ("Timeline",      "right"),
        "notifications": ("Notifications", "right"),
        "logs":          ("Logs",          "bottom"),
    }

    def __init__(self, main_window: QMainWindow):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._main = main_window
        self._docks: Dict[str, DockPanel] = {}

    # ── Create ────────────────────────────────────────────────────────

    def create_dock(self, dock_id: str, title: str,
                    area: str = "left",
                    attach: bool = True) -> DockPanel:
        """Create and optionally attach a dock panel."""
        panel = DockPanel(dock_id, title, area)
        panel.build(self._main)
        self._docks[dock_id] = panel
        return panel

    def create_all(self, config: Optional[Dict[str, Tuple[str, str]]] = None) -> List[DockPanel]:
        """Create all standard dock panels from config."""
        cfg = config or self.DEFAULT_DOCKS
        panels = []
        for dock_id, (title, area) in cfg.items():
            panel = self.create_dock(dock_id, title, area)
            panels.append(panel)
        return panels

    # ── Attach / Detach ───────────────────────────────────────────────

    def attach(self, dock_id: str, area: str = "left") -> bool:
        """Attach a dock panel to the main window."""
        panel = self._docks.get(dock_id)
        if not panel:
            return False
        panel.attach_to(self._main, area)
        return True

    def detach(self, dock_id: str) -> bool:
        """Detach (float) a dock panel."""
        panel = self._docks.get(dock_id)
        if not panel:
            return False
        panel.detach()
        return True

    # ── Visibility ────────────────────────────────────────────────────

    def show(self, dock_id: str) -> bool:
        panel = self._docks.get(dock_id)
        if not panel:
            return False
        panel.show()
        return True

    def hide(self, dock_id: str) -> bool:
        panel = self._docks.get(dock_id)
        if not panel:
            return False
        panel.hide()
        return True

    def toggle(self, dock_id: str) -> Optional[bool]:
        """Toggle dock visibility. Returns new visible state or None."""
        panel = self._docks.get(dock_id)
        if not panel:
            return None
        new_visible = not (panel.is_visible or False)
        panel.set_visible(new_visible)
        return new_visible

    def set_visible(self, dock_id: str, visible: bool) -> bool:
        panel = self._docks.get(dock_id)
        if not panel:
            return False
        panel.set_visible(visible)
        return True

    # ── Layout bridge ─────────────────────────────────────────────────

    def apply_layout(self, layout) -> None:
        """Apply a DesktopLayout (Sprint 16 OP-205) to dock visibility.

        DesktopLayout has 4 regions: left, center, right, bottom.
        Maps region visibility to dock panels.
        """
        if not layout:
            return

        try:
            # Left panel -> navigation dock
            nav = self._docks.get("navigation")
            if nav and hasattr(layout, 'left_panel') and layout.left_panel:
                nav.set_visible(not getattr(layout.left_panel, 'collapsed', False))

            # Right panel -> timeline / notifications
            for did in ("timeline", "notifications"):
                dock = self._docks.get(did)
                if dock and hasattr(layout, 'right_panel') and layout.right_panel:
                    dock.set_visible(not getattr(layout.right_panel, 'collapsed', False))

            # Bottom panel -> logs
            logs = self._docks.get("logs")
            if logs and hasattr(layout, 'bottom_panel') and layout.bottom_panel:
                logs.set_visible(not getattr(layout.bottom_panel, 'collapsed', False))
        except Exception:
            pass

    # ── State persistence ────────────────────────────────────────────

    def save_state(self) -> dict:
        """Save dock state as a serializable dict."""
        state = {}
        for dock_id, panel in self._docks.items():
            q = panel.qdock
            if q:
                state[dock_id] = {
                    "visible": q.isVisible(),
                    "floating": q.isFloating(),
                    "geometry": (
                        q.x(), q.y(), q.width(), q.height()
                    ) if q.isFloating() else None,
                }
        return {"docks": state}

    def restore_state(self, state: dict) -> None:
        """Restore dock state from dict."""
        docks = state.get("docks", {})
        for dock_id, data in docks.items():
            panel = self._docks.get(dock_id)
            if not panel:
                continue
            panel.set_visible(data.get("visible", True))
            if data.get("floating") and data.get("geometry"):
                panel.detach()
                geo = data["geometry"]
                if panel.qdock and len(geo) == 4:
                    panel.qdock.setGeometry(*geo)

    # ── Access ────────────────────────────────────────────────────────

    def get_panel(self, dock_id: str) -> Optional[DockPanel]:
        return self._docks.get(dock_id)

    def get_qdock(self, dock_id: str) -> Optional[QDockWidget]:
        panel = self._docks.get(dock_id)
        return panel.qdock if panel else None

    def get_content(self, dock_id: str) -> Optional[QWidget]:
        panel = self._docks.get(dock_id)
        return panel.content if panel else None

    def set_content(self, dock_id: str, widget: QWidget) -> bool:
        panel = self._docks.get(dock_id)
        if not panel:
            return False
        panel.set_widget(widget)
        return True

    @property
    def dock_ids(self) -> List[str]:
        return list(self._docks.keys())

    @property
    def panels(self) -> Dict[str, DockPanel]:
        return self._docks

    def summary(self) -> str:
        visible = sum(1 for p in self._docks.values() if p.is_visible)
        return f"QtDockManager: {len(self._docks)} docks, {visible} visible"
