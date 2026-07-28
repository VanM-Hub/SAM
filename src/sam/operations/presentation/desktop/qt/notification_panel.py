"""NotificationPanel — Notification panel for the SAM Desktop.

Right-side panel. Supports: unread/read, priority, dismiss,
clear read, grouping. NotificationCenter is the data source.
"""

from __future__ import annotations

from typing import Optional, List, Callable, Dict, Set

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QListWidget, QListWidgetItem, QFrame,
        QComboBox, QMenu,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QColor, QBrush, QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False


class _NotificationItem:
    """Internal notification data — from DTO."""
    def __init__(self, notif_id: str, title: str, message: str,
                 priority: str = "normal", read: bool = False,
                 source: str = "", timestamp: str = "",
                 group: str = ""):
        self.notif_id = notif_id
        self.title = title
        self.message = message
        self.priority = priority
        self.read = read
        self.source = source
        self.timestamp = timestamp
        self.group = group


class NotificationPanel:
    """Notification panel with read/unread, priority, dismiss, grouping.

    NotificationCenter remains the data source.
    This widget only reads from bridge.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._parent = parent
        self._container: Optional[QWidget] = None
        self._list: Optional[QListWidget] = None

        # Controls
        self._group_cb: Optional[QComboBox] = None
        self._unread_count_lbl: Optional[QLabel] = None

        # State
        self._notifications: List[_NotificationItem] = []
        self._grouped: bool = False
        self._current_group: str = "all"

        # Callbacks
        self._on_dismiss: Optional[Callable[[str], None]] = None
        self._on_dismiss_all: Optional[Callable[[], None]] = None

    def build(self) -> QWidget:
        """Build the notification panel."""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Header
        header_layout = QHBoxLayout()

        count_lbl = QLabel("Notifications")
        header_layout.addWidget(count_lbl)
        self._unread_count_lbl = count_lbl

        # Group combo
        group_cb = QComboBox()
        group_cb.addItems(["all", "unread", "high priority"])
        group_cb.currentTextChanged.connect(self._on_group_changed)
        header_layout.addWidget(group_cb)
        self._group_cb = group_cb

        header_layout.addStretch()
        layout.addLayout(header_layout)

        # Action buttons
        action_layout = QHBoxLayout()

        dismiss_read_btn = QPushButton("Clear Read")
        dismiss_read_btn.clicked.connect(self._on_clear_read)
        action_layout.addWidget(dismiss_read_btn)

        dismiss_all_btn = QPushButton("Dismiss All")
        dismiss_all_btn.clicked.connect(self._on_dismiss_all_clicked)
        action_layout.addWidget(dismiss_all_btn)

        action_layout.addStretch()
        layout.addLayout(action_layout)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Notification list
        notif_list = QListWidget()
        notif_list.setAlternatingRowColors(True)
        notif_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        notif_list.customContextMenuRequested.connect(self._on_context_menu)
        notif_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(notif_list)
        self._list = notif_list

        if self._parent:
            self._parent.layout().addWidget(container)

        self._container = container
        return container

    # ── Data ─────────────────────────────────────────────────────────

    def set_notifications(self, notifications: List[Dict]) -> None:
        """Set notification data from DTO.

        Args:
            notifications: List of dicts with keys:
                id, title, message, priority, read, source, timestamp
        """
        self._notifications = [
            _NotificationItem(
                notif_id=str(n.get("id", "")),
                title=str(n.get("title", "")),
                message=str(n.get("message", "")),
                priority=str(n.get("priority", "normal")),
                read=bool(n.get("read", False)),
                source=str(n.get("source", "")),
                timestamp=str(n.get("timestamp", ""))[:19],
                group=str(n.get("group", n.get("source", ""))),
            )
            for n in notifications
        ]
        self._rebuild()

    def add_notification(self, notif: Dict) -> None:
        """Append a single notification."""
        item = _NotificationItem(
            notif_id=str(notif.get("id", "")),
            title=str(notif.get("title", "")),
            message=str(notif.get("message", "")),
            priority=str(notif.get("priority", "normal")),
            read=bool(notif.get("read", False)),
            source=str(notif.get("source", "")),
            timestamp=str(notif.get("timestamp", ""))[:19],
            group=str(notif.get("group", notif.get("source", ""))),
        )
        self._notifications.insert(0, item)
        self._rebuild()

    # ── Filters ──────────────────────────────────────────────────────

    def _on_group_changed(self, group: str) -> None:
        self._current_group = group
        self._rebuild()

    def _get_filtered(self) -> List[_NotificationItem]:
        group = self._current_group
        if group == "all":
            return list(self._notifications)
        elif group == "unread":
            return [n for n in self._notifications if not n.read]
        elif group == "high priority":
            return [n for n in self._notifications
                    if n.priority.lower() in ("high", "critical")]
        return list(self._notifications)

    # ── Actions ──────────────────────────────────────────────────────

    def _on_clear_read(self) -> None:
        """Dismiss all read notifications."""
        self._notifications = [n for n in self._notifications if not n.read]
        self._rebuild()
        self._update_count()

    def _on_dismiss_all_clicked(self) -> None:
        self._notifications.clear()
        self._rebuild()
        self._update_count()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Mark notification as read on click."""
        for n in self._notifications:
            if n.notif_id == item.data(Qt.ItemDataRole.UserRole):
                n.read = True
                break
        self._rebuild()
        self._update_count()

    def _on_dismiss_notification(self, notif_id: str) -> None:
        self._notifications = [n for n in self._notifications if n.notif_id != notif_id]
        self._rebuild()
        self._update_count()

    def _on_context_menu(self, pos) -> None:
        if not self._list:
            return
        item = self._list.itemAt(pos)
        if not item:
            return

        menu = QMenu()
        dismiss_action = menu.addAction("Dismiss")
        mark_read_action = menu.addAction("Mark Read")

        action = menu.exec_(self._list.viewport().mapToGlobal(pos))
        notif_id = item.data(Qt.ItemDataRole.UserRole)

        if action == dismiss_action:
            self._on_dismiss_notification(notif_id)
        elif action == mark_read_action:
            for n in self._notifications:
                if n.notif_id == notif_id:
                    n.read = True
                    break
            self._rebuild()

    # ── Internal ─────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        if not self._list:
            return
        self._list.clear()
        for n in self._get_filtered():
            text = f"[{n.priority.upper()}] {n.title}"
            if not n.read:
                text = f"* {text}"
            if n.timestamp:
                text = f"{n.timestamp} {text}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, n.notif_id)

            # Style: unread bold/colored, read normal
            if not n.read:
                f = item.font()
                f.setBold(True)
                item.setFont(f)

            # Priority colors
            if n.priority.lower() == "critical":
                item.setForeground(QBrush(QColor("#FF0000")))
            elif n.priority.lower() == "high":
                item.setForeground(QBrush(QColor("#FF8800")))
            elif not n.read:
                item.setForeground(QBrush(QColor("#FFFFFF")))

            self._list.addItem(item)

        self._update_count()

    def _update_count(self) -> None:
        unread = sum(1 for n in self._notifications if not n.read)
        if self._unread_count_lbl:
            text = f"Notifications ({unread} unread)" if unread > 0 else "Notifications"
            self._unread_count_lbl.setText(text)

    # ── Callbacks ────────────────────────────────────────────────────

    def on_dismiss(self, handler: Callable[[str], None]) -> None:
        self._on_dismiss = handler

    # ── Access ───────────────────────────────────────────────────────

    @property
    def widget(self) -> Optional[QWidget]:
        return self._container

    @property
    def notification_count(self) -> int:
        return len(self._notifications)

    @property
    def unread_count(self) -> int:
        return sum(1 for n in self._notifications if not n.read)

    def clear(self) -> None:
        self._notifications.clear()
        self._rebuild()

    def summary(self) -> str:
        return f"NotificationPanel: {self.unread_count} unread / {len(self._notifications)} total"
