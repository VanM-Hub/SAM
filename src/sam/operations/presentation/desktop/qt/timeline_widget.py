"""TimelineWidget — Event timeline for the SAM Desktop.

QTreeWidget with columns: Severity, Time, Mission, Description.
Supports: search, filter, follow, auto-scroll, copy row.
Data from DTO via bridge pipeline. No direct query.
"""

from __future__ import annotations

from typing import Optional, List, Callable, Dict, Set

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QTreeWidget, QTreeWidgetItem,
        QLineEdit, QComboBox, QHBoxLayout, QLabel, QPushButton,
        QCheckBox, QMenu,
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QClipboard, QColor, QBrush
    HAS_QT = True
except ImportError:
    HAS_QT = False


class TimelineWidget:
    """Event timeline widget.

    Columns: Severity, Time, Mission, Description.
    Supports: search, filter by level, follow (auto-scroll),
              auto-scroll on new, copy row.
    No business logic. Data from DTO via bridge.
    """

    HEADERS = ["", "Time", "Mission", "Description"]

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._parent = parent
        self._container: Optional[QWidget] = None
        self._tree: Optional[QTreeWidget] = None

        # Controls
        self._search_input: Optional[QLineEdit] = None
        self._level_filter: Optional[QComboBox] = None
        self._follow_check: Optional[QCheckBox] = None

        # State
        self._follow = True
        self._paused = False
        self._events: List[Dict] = []
        self._max_events = 500

        # Timer for auto-scroll
        self._auto_scroll_timer: Optional[QTimer] = None

    def build(self) -> QWidget:
        """Build the timeline widget."""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Toolbar
        toolbar = QHBoxLayout()

        # Search
        search_label = QLabel("Search:")
        toolbar.addWidget(search_label)
        search = QLineEdit()
        search.setPlaceholderText("Search events...")
        search.textChanged.connect(self._on_search_changed)
        toolbar.addWidget(search)
        self._search_input = search

        # Level filter
        level_label = QLabel("Level:")
        toolbar.addWidget(level_label)
        level_cb = QComboBox()
        level_cb.addItems(["all", "info", "warning", "error", "critical", "debug"])
        level_cb.currentTextChanged.connect(self._on_level_changed)
        toolbar.addWidget(level_cb)
        self._level_filter = level_cb

        # Follow checkbox
        follow = QCheckBox("Follow")
        follow.setChecked(True)
        follow.toggled.connect(self._on_follow_toggled)
        toolbar.addWidget(follow)
        self._follow_check = follow

        # Pause/Resume button
        pause_btn = QPushButton("Pause")
        pause_btn.setCheckable(True)
        pause_btn.toggled.connect(lambda checked: pause_btn.setText(
            "Resume" if checked else "Pause"))
        pause_btn.toggled.connect(self._on_pause_toggled)
        toolbar.addWidget(pause_btn)

        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Tree widget
        tree = QTreeWidget()
        tree.setHeaderLabels(self.HEADERS)
        tree.setColumnCount(4)
        tree.setColumnWidth(0, 28)   # Severity icon area
        tree.setColumnWidth(1, 160)  # Time
        tree.setColumnWidth(2, 140)  # Mission
        tree.setColumnWidth(3, 400)  # Description
        tree.setAlternatingRowColors(True)
        tree.setRootIsDecorated(False)
        tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        tree.customContextMenuRequested.connect(self._on_context_menu)

        # Sort by time (default ascending = newest at bottom)
        tree.sortByColumn(1, Qt.SortOrder.AscendingOrder)
        tree.header().setStretchLastSection(True)

        layout.addWidget(tree)
        self._tree = tree

        if self._parent:
            self._parent.layout().addWidget(container)

        self._container = container
        return container

    # ── Core data ────────────────────────────────────────────────────

    def set_events(self, events: List[Dict]) -> None:
        """Set event data from DTO.

        Args:
            events: List of dicts with keys:
                severity (str), time (str), mission_id (str),
                description (str)
        """
        self._events = events
        self._rebuild()

    def append_event(self, event: Dict) -> None:
        """Append a single event and auto-scroll."""
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        self._add_event_item(event)

        if self._follow and not self._paused:
            self._scroll_to_bottom()

    def clear(self) -> None:
        self._events = []
        if self._tree:
            self._tree.clear()

    # ── Internal ─────────────────────────────────────────────────────

    def _rebuild(self) -> None:
        if not self._tree:
            return
        self._tree.clear()
        for event in self._events:
            self._add_event_item(event)

        if self._follow and not self._paused:
            self._scroll_to_bottom()

    def _add_event_item(self, event: Dict) -> None:
        if not self._tree:
            return
        severity = str(event.get("severity", event.get("level", "info")))
        timestamp = str(event.get("time", event.get("timestamp", "")))
        mission = str(event.get("mission_id", event.get("mission", "")))
        description = str(event.get("description", event.get("message", "")))

        # Apply filter
        level_filter = self._level_filter.currentText() if self._level_filter else "all"
        if level_filter != "all" and severity.lower() != level_filter:
            return

        search = self._search_input.text().lower() if self._search_input else ""
        if search and search not in description.lower() and search not in mission.lower():
            return

        item = QTreeWidgetItem(self._tree, ["", timestamp, mission, description])

        # Severity icon (text-based since no icons)
        severity_icons = {
            "critical": "!!",
            "error": "!!",
            "warning": "!",
            "info": "i",
            "debug": ".",
        }
        icon_text = severity_icons.get(severity.lower(), "?")
        item.setText(0, icon_text)

        # Color-code severity
        color_map = {
            "critical": QColor("#FF0000"),
            "error": QColor("#FF4444"),
            "warning": QColor("#FFAA00"),
            "info": QColor("#888888"),
            "debug": QColor("#555555"),
        }
        color = color_map.get(severity.lower())
        if color:
            item.setForeground(0, QBrush(color))

        # Store severity data for filtering
        item.setData(0, Qt.ItemDataRole.UserRole, severity)

    def _scroll_to_bottom(self) -> None:
        if self._tree and self._tree.topLevelItemCount() > 0:
            last = self._tree.topLevelItem(self._tree.topLevelItemCount() - 1)
            self._tree.scrollToItem(last)

    # ── Filter / Search ──────────────────────────────────────────────

    def _on_search_changed(self, text: str) -> None:
        self._rebuild()

    def _on_level_changed(self, level: str) -> None:
        self._rebuild()

    def _on_follow_toggled(self, checked: bool) -> None:
        self._follow = checked
        if checked and not self._paused:
            self._scroll_to_bottom()

    def _on_pause_toggled(self, paused: bool) -> None:
        self._paused = paused

    # ── Context menu ─────────────────────────────────────────────────

    def _on_context_menu(self, pos) -> None:
        if not self._tree:
            return
        item = self._tree.itemAt(pos)
        if not item:
            return

        menu = QMenu()
        copy_action = menu.addAction("Copy Row")
        action = menu.exec_(self._tree.viewport().mapToGlobal(pos))
        if action == copy_action:
            self._copy_row(item)

    def _copy_row(self, item: QTreeWidgetItem) -> None:
        """Copy the row as tab-separated text to clipboard."""
        parts = []
        for i in range(item.columnCount()):
            parts.append(item.text(i))
        text = "\t".join(parts)

        from PySide6.QtWidgets import QApplication
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    # ── Feature access ───────────────────────────────────────────────

    def set_follow(self, follow: bool) -> None:
        self._follow = follow
        if self._follow_check:
            self._follow_check.setChecked(follow)

    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    @property
    def is_following(self) -> bool:
        return self._follow

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def widget(self) -> Optional[QWidget]:
        return self._container

    @property
    def event_count(self) -> int:
        if self._tree:
            return self._tree.topLevelItemCount()
        return 0

    def summary(self) -> str:
        return (
            f"TimelineWidget: {self.event_count} events shown, "
            f"{'following' if self._follow else 'paused'}"
        )
