"""ToolbarActions — Toolbar action definitions for SAM Desktop.

All actions produce InteractionCommands sent to the dispatcher.
No business logic. No domain access. Presentation only.
"""

from __future__ import annotations

from typing import Optional, Dict, List, Callable

try:
    from PySide6.QtWidgets import (
        QToolBar, QAction, QWidget, QMainWindow,
        QPushButton, QHBoxLayout, QLabel, QMenu,
        QStyle,
    )
    from PySide6.QtCore import Qt, Signal, QObject
    from PySide6.QtGui import QIcon, QKeySequence
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QObject = object
    Signal = lambda *a, **kw: None


# ── Action IDs ───────────────────────────────────────────────────────

class ActionId:
    """Canonical action identifiers for toolbar actions."""
    REFRESH = "toolbar.refresh"
    PAUSE_REFRESH = "toolbar.pause_refresh"
    RESUME_REFRESH = "toolbar.resume_refresh"
    THEME = "toolbar.theme"
    EXPORT = "toolbar.export"
    APPROVAL = "toolbar.approval"
    MISSION = "toolbar.mission"
    TIMELINE = "toolbar.timeline"
    NOTIFICATIONS = "toolbar.notifications"
    DASHBOARD = "toolbar.dashboard"
    SETTINGS = "toolbar.settings"
    HELP = "toolbar.help"
    SEARCH = "toolbar.search"
    PROFILE = "toolbar.profile"
    TERMINAL = "toolbar.terminal"
    PROFILE_SWITCH = "toolbar.profile_switch"


# ── Action definition ────────────────────────────────────────────────

class ToolbarActionDef:
    """Immutable definition of a toolbar action."""

    def __init__(self, action_id: str, label: str,
                 shortcut: str = "",
                 tooltip: str = "",
                 icon_name: str = ""):
        self.id = action_id
        self.label = label
        self.shortcut = shortcut
        self.tooltip = tooltip
        self.icon_name = icon_name

    def to_interaction_command(self) -> dict:
        """Convert to an InteractionCommand dict."""
        return {
            "action": self.id,
            "type": "toolbar",
            "source": "toolbar",
            "label": self.label,
        }


# ── Built-in action definitions ──────────────────────────────────────

_BUILTIN_ACTIONS = [
    ToolbarActionDef(ActionId.REFRESH, "Refresh", "F5",
                     "Refresh all panels"),
    ToolbarActionDef(ActionId.PAUSE_REFRESH, "Pause", "",
                     "Pause auto-refresh"),
    ToolbarActionDef(ActionId.RESUME_REFRESH, "Resume", "",
                     "Resume auto-refresh"),
    ToolbarActionDef(ActionId.THEME, "Theme", "",
                     "Switch theme"),
    ToolbarActionDef(ActionId.PROFILE_SWITCH, "Profile", "",
                     "Switch workspace profile"),
    ToolbarActionDef(ActionId.EXPORT, "Export", "Ctrl+E",
                     "Export report"),
    ToolbarActionDef(ActionId.DASHBOARD, "Dashboard", "Ctrl+D",
                     "Go to Dashboard"),
    ToolbarActionDef(ActionId.MISSION, "Missions", "Ctrl+M",
                     "Go to Missions"),
    ToolbarActionDef(ActionId.TIMELINE, "Timeline", "Ctrl+T",
                     "Go to Timeline"),
    ToolbarActionDef(ActionId.NOTIFICATIONS, "Notifications", "Ctrl+N",
                     "Go to Notifications"),
    ToolbarActionDef(ActionId.APPROVAL, "Approvals", "Ctrl+P",
                     "Go to Approvals"),
    ToolbarActionDef(ActionId.TERMINAL, "Terminal", "Ctrl+`",
                     "Toggle Terminal"),
    ToolbarActionDef(ActionId.SEARCH, "Search", "Ctrl+Shift+F",
                     "Search everything"),
    ToolbarActionDef(ActionId.SETTINGS, "Settings", "Ctrl+,",
                     "Open settings"),
    ToolbarActionDef(ActionId.HELP, "Help", "F1",
                     "Open help"),
]


# ── Toolbar Actions Widget ───────────────────────────────────────────

class ToolbarActions(QObject):
    """Toolbar action manager for SAM Desktop.

    Manages QActions in a QToolBar. All actions emit InteractionCommands.
    Separate QToolBar instance is managed by the caller.
    """

    action_triggered = Signal(str)  # emits action_id

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        super().__init__(parent)
        self._actions: Dict[str, QAction] = {}
        self._main_toolbar: Optional[QToolBar] = None

    def build(self, toolbar: QToolBar) -> None:
        """Populate the given QToolBar with standard actions."""
        self._main_toolbar = toolbar
        toolbar.setMovable(False)
        toolbar.setToolButtonStyle(Qt.ToolButtonStyle.ToolButtonTextBesideIcon)

        for action_def in _BUILTIN_ACTIONS:
            qaction = QAction(action_def.label, toolbar)
            qaction.setToolTip(action_def.tooltip or action_def.label)
            if action_def.shortcut:
                qaction.setShortcut(QKeySequence(action_def.shortcut))
            qaction.setData(action_def.id)

            # Icon from standard pixmaps
            icon_map = {
                ActionId.REFRESH: "SP_BrowserReload",
                ActionId.SETTINGS: "SP_ComputerIcon",
                ActionId.HELP: "SP_DialogHelpButton",
                ActionId.SEARCH: "SP_FileDialogDetailedView",
            }
            icon_key = icon_map.get(action_def.id)
            if icon_key:
                pixmap = getattr(QStyle.StandardPixmap, icon_key, None)
                if pixmap:
                    qaction.setIcon(toolbar.style().standardIcon(pixmap))

            qaction.triggered.connect(lambda checked, aid=action_def.id:
                                      self.action_triggered.emit(aid))
            toolbar.addAction(qaction)
            self._actions[action_def.id] = qaction

    def add_custom_action(self, action_def: ToolbarActionDef,
                          handler: Optional[Callable] = None) -> None:
        """Add a custom action to the toolbar."""
        if not self._main_toolbar:
            return
        qaction = QAction(action_def.label, self._main_toolbar)
        qaction.setToolTip(action_def.tooltip or action_def.label)
        if action_def.shortcut:
            qaction.setShortcut(QKeySequence(action_def.shortcut))
        qaction.setData(action_def.id)

        if handler:
            qaction.triggered.connect(handler)
        else:
            qaction.triggered.connect(
                lambda checked, aid=action_def.id:
                self.action_triggered.emit(aid))

        self._main_toolbar.addAction(qaction)
        self._actions[action_def.id] = qaction

    def add_separator(self) -> None:
        """Add a separator to the toolbar."""
        if self._main_toolbar:
            self._main_toolbar.addSeparator()

    # ── Action control ───────────────────────────────────────────────

    def enable_action(self, action_id: str, enabled: bool = True) -> None:
        qaction = self._actions.get(action_id)
        if qaction:
            qaction.setEnabled(enabled)

    def set_action_visible(self, action_id: str, visible: bool = True) -> None:
        qaction = self._actions.get(action_id)
        if qaction:
            qaction.setVisible(visible)

    def set_action_text(self, action_id: str, text: str) -> None:
        qaction = self._actions.get(action_id)
        if qaction:
            qaction.setText(text)

    def get_action(self, action_id: str) -> Optional[QAction]:
        return self._actions.get(action_id)

    @property
    def action_count(self) -> int:
        return len(self._actions)

    def broadcast_state(self, state: dict) -> None:
        """Update toolbar state from a state dict.

        Keys: paused (bool), theme (str), profile (str), etc.
        """
        if state.get("paused"):
            resume = self._actions.get(ActionId.RESUME_REFRESH)
            pause = self._actions.get(ActionId.PAUSE_REFRESH)
            if resume:
                resume.setVisible(True)
            if pause:
                pause.setVisible(False)
            refresh = self._actions.get(ActionId.REFRESH)
            if refresh:
                refresh.setText("Resume")

    # ── Definitions ──────────────────────────────────────────────────

    @staticmethod
    def builtin_action_defs() -> List[ToolbarActionDef]:
        return list(_BUILTIN_ACTIONS)

    @staticmethod
    def get_action_def(action_id: str) -> Optional[ToolbarActionDef]:
        for a in _BUILTIN_ACTIONS:
            if a.id == action_id:
                return a
        return None

    def summary(self) -> str:
        return (
            f"ToolbarActions: {len(self._actions)} actions registered"
        )
