"""TimelineExplorer — Enhanced timeline explorer for SAM Desktop.

Extends TimelineWidget with: filter by severity/mission/source,
keyword search, jump to event, copy/export, follow mode.
All data from DTO via bridge. No direct query.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Callable
from datetime import datetime

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QTreeWidget,
        QTreeWidgetItem, QLineEdit, QComboBox, QPushButton,
        QLabel, QCheckBox, QMenu, QMessageBox, QApplication,
        QHeaderView,
    )
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QBrush, QClipboard, QAction
    HAS_QT = True
except ImportError:
    HAS_QT = False


# ── Helper: classify severity ────────────────────────────────────────

SEVERITY_ORDER = {"critical": 0, "error": 1, "warning": 2,
                  "info": 3, "debug": 4, "unknown": 5}

SEVERITY_COLORS = {
    "critical": QColor("#FF0000"),
    "error": QColor("#FF4444"),
    "warning": QColor("#FFAA00"),
    "info": QColor("#888888"),
    "debug": QColor("#555555"),
    "unknown": QColor("#888888"),
}

SEVERITY_ICONS = {
    "critical": "!!",
    "error": "!",
    "warning": "?",
    "info": "i",
    "debug": ".",
    "unknown": "?",
}


class TimelineExplorer(QWidget):
    """Enhanced timeline explorer.

    Columns: Marker, Severity, Time, Mission, Source, Description.
    Supports: multi-filter, keyword search, jump, copy, export, follow.
    """

    COLUMNS = ["", "Severity", "Time", "Mission", "Source", "Description"]
    COL_WIDTHS = [24, 70, 160, 120, 100, 400]

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        super().__init__(parent)

        # State
        self._events: List[Dict] = []
        self._filter_severity = "all"
        self._filter_mission = "all"
        self._filter_source = "all"
        self._filter_keyword = ""
        self._follow = True
        self._paused = False
        self._max_events = 2000

        # External callbacks
        self._on_jump: Optional[Callable[[str], None]] = None  # jump to mission
        self._on_export: Optional[Callable[[List[Dict]], None]] = None

        # Debounce timer for search
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.setInterval(300)
        self._debounce_timer.timeout.connect(self._rebuild)

        # UI
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ── Filter bar ──────────────────────────────────────────────
        filter_bar = QHBoxLayout()

        # Keyword search
        filter_bar.addWidget(QLabel("Search:"))
        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search events...")
        self._search_input.setMinimumWidth(150)
        self._search_input.textChanged.connect(
            lambda: self._debounce_timer.start())
        filter_bar.addWidget(self._search_input)

        # Severity filter
        filter_bar.addWidget(QLabel("Severity:"))
        self._severity_filter = QComboBox()
        self._severity_filter.addItems(
            ["all", "critical", "error", "warning", "info", "debug"])
        self._severity_filter.currentTextChanged.connect(self._rebuild)
        filter_bar.addWidget(self._severity_filter)

        # Mission filter
        filter_bar.addWidget(QLabel("Mission:"))
        self._mission_filter = QComboBox()
        self._mission_filter.addItem("all")
        self._mission_filter.setMinimumWidth(120)
        self._mission_filter.currentTextChanged.connect(self._rebuild)
        filter_bar.addWidget(self._mission_filter)

        # Source filter
        filter_bar.addWidget(QLabel("Source:"))
        self._source_filter = QComboBox()
        self._source_filter.addItem("all")
        self._source_filter.setMinimumWidth(100)
        self._source_filter.currentTextChanged.connect(self._rebuild)
        filter_bar.addWidget(self._source_filter)

        # Follow toggle
        self._follow_cb = QCheckBox("Follow")
        self._follow_cb.setChecked(True)
        self._follow_cb.toggled.connect(self._on_follow_toggled)
        filter_bar.addWidget(self._follow_cb)

        # Pause button
        self._pause_btn = QPushButton("Pause")
        self._pause_btn.setCheckable(True)
        self._pause_btn.toggled.connect(self._on_pause_toggled)
        filter_bar.addWidget(self._pause_btn)

        self._clear_btn = QPushButton("Clear")
        self._clear_btn.clicked.connect(self.clear)
        filter_bar.addWidget(self._clear_btn)

        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # ── Tree widget ────────────────────────────────────────────
        self._tree = QTreeWidget()
        self._tree.setHeaderLabels(self.COLUMNS)
        self._tree.setColumnCount(len(self.COLUMNS))
        for i, w in enumerate(self.COL_WIDTHS):
            self._tree.setColumnWidth(i, w)
        self._tree.setAlternatingRowColors(True)
        self._tree.setRootIsDecorated(False)
        self._tree.setSortingEnabled(True)
        self._tree.sortByColumn(2, Qt.SortOrder.AscendingOrder)
        self._tree.header().setStretchLastSection(True)

        # Context menu
        self._tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._tree.customContextMenuRequested.connect(self._on_context_menu)

        # Double-click → jump
        self._tree.itemDoubleClicked.connect(self._on_double_click)

        layout.addWidget(self._tree)

        # ── Status bar ──────────────────────────────────────────────
        self._status_label = QLabel("0 events shown")
        layout.addWidget(self._status_label)

    # ── Data ─────────────────────────────────────────────────────────

    def set_events(self, events: List[Dict]) -> None:
        """Set event data from DTO."""
        self._events = events
        self._update_filters()
        self._rebuild()

    def append_event(self, event: Dict) -> None:
        """Append a single event."""
        self._events.append(event)
        if len(self._events) > self._max_events:
            self._events = self._events[-self._max_events:]

        if self._follow and not self._paused:
            self._add_event_item(event)
            self._scroll_to_bottom()
            self._update_status()

    def set_max_events(self, max_count: int) -> None:
        self._max_events = max_count

    def clear(self) -> None:
        self._events = []
        if self._tree:
            self._tree.clear()
        self._update_status()

    # ── Event building ───────────────────────────────────────────────

    def _add_event_item(self, event: Dict) -> None:
        """Add a single event item to the tree (no filter check)."""
        if not self._tree:
            return

        severity = str(event.get("severity", event.get("level", "info"))).lower()
        timestamp = str(event.get("time", event.get("timestamp", "")))
        mission = str(event.get("mission_id", event.get("mission", "")))
        source = str(event.get("source", event.get("component", "")))
        description = str(event.get("description", event.get("message", "")))

        item = QTreeWidgetItem(self._tree, [
            SEVERITY_ICONS.get(severity, "?"),
            severity.capitalize(),
            timestamp,
            mission,
            source,
            description,
        ])

        # Color severity cell
        color = SEVERITY_COLORS.get(severity)
        if color:
            item.setForeground(0, QBrush(color))
            item.setForeground(1, QBrush(color))

        # Store data for later use
        item.setData(0, Qt.ItemDataRole.UserRole, severity)

    def _rebuild(self) -> None:
        """Rebuild the tree from filtered events."""
        if not self._tree:
            return
        self._tree.clear()

        keyword = self._search_input.text().lower() if self._search_input else ""
        severity_filter = self._severity_filter.currentText() if self._severity_filter else "all"
        mission_filter = self._mission_filter.currentText() if self._mission_filter else "all"
        source_filter = self._source_filter.currentText() if self._source_filter else "all"

        count = 0
        for event in self._events:
            sev = str(event.get("severity", event.get("level", "info"))).lower()
            mis = str(event.get("mission_id", event.get("mission", "")))
            src = str(event.get("source", event.get("component", "")))
            desc = str(event.get("description", event.get("message", "")))

            # Apply filters
            if severity_filter != "all" and sev != severity_filter:
                continue
            if mission_filter != "all" and mis != mission_filter:
                continue
            if source_filter != "all" and src != source_filter:
                continue
            if keyword and keyword not in desc.lower() and keyword not in mis.lower() and keyword not in sev.lower():
                continue

            self._add_event_item(event)
            count += 1

        if self._follow and not self._paused and count > 0:
            self._scroll_to_bottom()

        self._update_status()

    def _scroll_to_bottom(self) -> None:
        if self._tree and self._tree.topLevelItemCount() > 0:
            last = self._tree.topLevelItem(self._tree.topLevelItemCount() - 1)
            self._tree.scrollToItem(last)

    def _update_status(self) -> None:
        total = len(self._events)
        shown = self._tree.topLevelItemCount() if self._tree else 0
        paused = " [PAUSED]" if self._paused else ""
        self._status_label.setText(
            f"{shown} of {total} events shown{paused}")

    # ── Filter updates ───────────────────────────────────────────────

    def _update_filters(self) -> None:
        """Update mission and source filter dropdowns."""
        missions = set()
        sources = set()
        for ev in self._events:
            mis = str(ev.get("mission_id", ev.get("mission", "")))
            src = str(ev.get("source", ev.get("component", "")))
            if mis:
                missions.add(mis)
            if src:
                sources.add(src)

        # Update mission filter
        current_mission = self._mission_filter.currentText()
        self._mission_filter.blockSignals(True)
        self._mission_filter.clear()
        self._mission_filter.addItem("all")
        for m in sorted(missions):
            self._mission_filter.addItem(m)
        idx = self._mission_filter.findText(current_mission)
        if idx >= 0:
            self._mission_filter.setCurrentIndex(idx)
        self._mission_filter.blockSignals(False)

        # Update source filter
        current_source = self._source_filter.currentText()
        self._source_filter.blockSignals(True)
        self._source_filter.clear()
        self._source_filter.addItem("all")
        for s in sorted(sources):
            self._source_filter.addItem(s)
        idx = self._source_filter.findText(current_source)
        if idx >= 0:
            self._source_filter.setCurrentIndex(idx)
        self._source_filter.blockSignals(False)

    def _on_follow_toggled(self, checked: bool) -> None:
        self._follow = checked
        if checked and not self._paused:
            self._scroll_to_bottom()

    def _on_pause_toggled(self, paused: bool) -> None:
        self._paused = paused
        self._pause_btn.setText("Resume" if paused else "Pause")
        self._update_status()

    # ── Jump / Navigation ────────────────────────────────────────────

    def set_on_jump(self, handler: Callable[[str], None]) -> None:
        """Set handler for jump-to-mission."""
        self._on_jump = handler

    def set_on_export(self, handler: Callable[[List[Dict]], None]) -> None:
        """Set handler for export."""
        self._on_export = handler

    def _on_double_click(self, item: QTreeWidgetItem, column: int) -> None:
        """Double-click: jump to mission."""
        if not self._on_jump:
            return
        mission_id = item.text(3) if item.columnCount() > 3 else ""
        if mission_id:
            self._on_jump(mission_id)

    def _get_item_event(self, item: QTreeWidgetItem) -> Optional[Dict]:
        """Reconstruct event dict from tree item."""
        if not item:
            return None
        return {
            "severity": item.text(1).lower() if item.columnCount() > 1 else "info",
            "time": item.text(2) if item.columnCount() > 2 else "",
            "mission_id": item.text(3) if item.columnCount() > 3 else "",
            "source": item.text(4) if item.columnCount() > 4 else "",
            "description": item.text(5) if item.columnCount() > 5 else "",
        }

    def _get_selected_events(self) -> List[Dict]:
        """Get event dicts for all selected items."""
        items = self._tree.selectedItems()
        return [self._get_item_event(it) for it in items if it]

    # ── Context menu ─────────────────────────────────────────────────

    def _on_context_menu(self, pos) -> None:
        item = self._tree.itemAt(pos)
        if not item:
            return

        menu = QMenu(self)

        # Copy actions
        copy_row = menu.addAction("Copy Row")
        copy_severity = menu.addAction("Copy Severity")
        copy_desc = menu.addAction("Copy Description")

        menu.addSeparator()

        # Jump
        jump_mission = menu.addAction("Jump to Mission")
        jump_mission.setEnabled(bool(self._on_jump))

        menu.addSeparator()

        # Export
        export_selected = menu.addAction("Export Selected")
        export_all = menu.addAction("Export All Visible")

        # Execute
        action = menu.exec_(self._tree.viewport().mapToGlobal(pos))
        if not action:
            return

        if action == copy_row:
            self._copy_to_clipboard(item)
        elif action == copy_severity:
            self._copy_text(item.text(1))
        elif action == copy_desc:
            self._copy_text(item.text(5) if item.columnCount() > 5 else "")
        elif action == jump_mission:
            if self._on_jump:
                mission_id = item.text(3) if item.columnCount() > 3 else ""
                if mission_id:
                    self._on_jump(mission_id)
        elif action == export_selected:
            self._export_events(self._get_selected_events())
        elif action == export_all:
            self._export_visible()

    def _copy_to_clipboard(self, item: QTreeWidgetItem) -> None:
        parts = []
        for i in range(item.columnCount()):
            parts.append(item.text(i))
        text = "\t".join(parts)

        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def _copy_text(self, text: str) -> None:
        clipboard = QApplication.clipboard()
        clipboard.setText(text)

    def _export_events(self, events: List[Dict]) -> None:
        if self._on_export:
            self._on_export(events)
        elif events:
            from .export_center import ExportCenter
            ExportCenter(self).export_raw("timeline", events)

    def _export_visible(self) -> None:
        """Export all visible (filtered) events."""
        events = []
        for i in range(self._tree.topLevelItemCount()):
            item = self._tree.topLevelItem(i)
            ev = self._get_item_event(item)
            if ev:
                events.append(ev)
        self._export_events(events)

    # ── Navigation ───────────────────────────────────────────────────

    def set_follow(self, follow: bool) -> None:
        self._follow = follow
        if self._follow_cb:
            self._follow_cb.setChecked(follow)

    def set_paused(self, paused: bool) -> None:
        self._paused = paused

    @property
    def is_following(self) -> bool:
        return self._follow

    @property
    def is_paused(self) -> bool:
        return self._paused

    @property
    def event_count(self) -> int:
        return self._tree.topLevelItemCount() if self._tree else 0

    @property
    def total_events(self) -> int:
        return len(self._events)

    def summary(self) -> str:
        return (
            f"TimelineExplorer: {self.event_count}/{self.total_events} events, "
            f"{'following' if self._follow else 'paused'}"
        )
