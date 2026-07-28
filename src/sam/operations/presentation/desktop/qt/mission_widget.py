"""MissionTableWidget — Mission table view for the SAM Desktop.

QTableView with columns: Mission ID, Status, Priority, Progress, Owner,
Started, Elapsed. Supports sort, filter, selection, double-click.
Data from DTO via bridge pipeline: no direct query.
"""

from __future__ import annotations

from typing import Optional, List, Callable, Dict, Tuple

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QTableView, QHeaderView,
        QLineEdit, QComboBox, QHBoxLayout, QLabel,
    )
    from PySide6.QtCore import Qt, QAbstractTableModel, QModelIndex, Signal
    from PySide6.QtGui import QColor, QBrush
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QAbstractTableModel = object


class _MissionData:
    """Internal mission row data — from DTO, no domain."""
    def __init__(self, mission_id: str, status: str, priority: str,
                 progress: str, owner: str, started: str, elapsed: str):
        self.mission_id = mission_id
        self.status = status
        self.priority = priority
        self.progress = progress
        self.owner = owner
        self.started = started
        self.elapsed = elapsed


class _MissionTableModel(QAbstractTableModel):
    """Table model for mission data (no direct DTO access)."""

    HEADERS = ["Mission ID", "Status", "Priority", "Progress",
               "Owner", "Started", "Elapsed"]

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        self._data: List[_MissionData] = []
        self._filtered: List[_MissionData] = list(self._data)
        self._filter_text = ""
        self._filter_status = "all"
        self._sort_col = -1
        self._sort_order = Qt.SortOrder.AscendingOrder

    def rowCount(self, parent=QModelIndex()) -> int:
        return len(self._filtered)

    def columnCount(self, parent=QModelIndex()) -> int:
        return len(self.HEADERS)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole):
        if not index.isValid():
            return None
        row = self._filtered[index.row()]
        col = index.column()

        if role == Qt.ItemDataRole.DisplayRole:
            vals = [
                row.mission_id, row.status, row.priority, row.progress,
                row.owner, row.started, row.elapsed,
            ]
            return vals[col] if col < len(vals) else ""

        if role == Qt.ItemDataRole.ForegroundRole:
            # Color-code status
            if col == 1:  # Status column
                color_map = {
                    "running": QColor("#00AA00"),
                    "completed": QColor("#888888"),
                    "failed": QColor("#FF4444"),
                    "pending": QColor("#FFAA00"),
                    "blocked": QColor("#FF0000"),
                    "paused": QColor("#AAAAAA"),
                }
                for key, color in color_map.items():
                    if key in row.status.lower():
                        return QBrush(color)

            # Color-code priority
            if col == 2:
                priority_map = {
                    "critical": QColor("#FF0000"),
                    "high": QColor("#FF8800"),
                    "normal": QColor("#00AA00"),
                }
                for key, color in priority_map.items():
                    if key == row.priority.lower():
                        return QBrush(color)

        return None

    def headerData(self, section: int, orientation, role: int = Qt.ItemDataRole.DisplayRole):
        if orientation == Qt.Orientation.Horizontal and role == Qt.ItemDataRole.DisplayRole:
            return self.HEADERS[section] if section < len(self.HEADERS) else ""
        if orientation == Qt.Orientation.Vertical and role == Qt.ItemDataRole.DisplayRole:
            return section + 1
        return None

    def sort(self, column: int, order: Qt.SortOrder = Qt.SortOrder.AscendingOrder) -> None:
        self.layoutAboutToBeChanged.emit()
        self._data.sort(key=lambda r: self._sort_key(r, column),
                        reverse=order == Qt.SortOrder.DescendingOrder)
        self._sort_col = column
        self._sort_order = order
        self._apply_filters()
        self.layoutChanged.emit()

    def _sort_key(self, row: _MissionData, col: int) -> str:
        vals = [row.mission_id, row.status, row.priority, row.progress,
                row.owner, row.started, row.elapsed]
        return vals[col] if col < len(vals) else ""

    def _apply_filters(self) -> None:
        self._filtered = [
            r for r in self._data
            if self._matches_filter(r)
        ]

    def _matches_filter(self, row: _MissionData) -> bool:
        if self._filter_text:
            text = self._filter_text.lower()
            if text not in row.mission_id.lower() and text not in row.owner.lower():
                return False
        if self._filter_status != "all":
            if self._filter_status != row.status.lower():
                return False
        return True

    def set_filter_text(self, text: str) -> None:
        self._filter_text = text
        self._apply_filters()
        self.layoutChanged.emit()

    def set_filter_status(self, status: str) -> None:
        self._filter_status = status
        self._apply_filters()
        self.layoutChanged.emit()

    def set_data(self, data: List[_MissionData]) -> None:
        self.beginResetModel()
        self._data = data
        self._apply_filters()
        if self._sort_col >= 0:
            self._filtered.sort(key=lambda r: self._sort_key(r, self._sort_col),
                                reverse=self._sort_order == Qt.SortOrder.DescendingOrder)
        self.endResetModel()

    def get_row_data(self, row: int) -> Optional[_MissionData]:
        if 0 <= row < len(self._filtered):
            return self._filtered[row]
        return None


class MissionTableWidget:
    """Mission table view with sort, filter, selection, double-click.

    Data from DTO via bridge pipeline. No direct query.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._parent = parent
        self._container: Optional[QWidget] = None

        # Model
        self._model = _MissionTableModel()

        # View
        self._table: Optional[QTableView] = None

        # Filter controls
        self._search_input: Optional[QLineEdit] = None
        self._status_filter: Optional[QComboBox] = None

        # Callbacks
        self._on_selection: Optional[Callable[[str], None]] = None
        self._on_double_click: Optional[Callable[[str], None]] = None

    def build(self) -> QWidget:
        """Build the mission table view."""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Filter bar
        filter_bar = QHBoxLayout()

        filter_label = QLabel("Search:")
        filter_bar.addWidget(filter_label)

        search = QLineEdit()
        search.setPlaceholderText("Search mission ID or owner...")
        search.textChanged.connect(self._on_search_changed)
        filter_bar.addWidget(search)
        self._search_input = search

        status_label = QLabel("Status:")
        filter_bar.addWidget(status_label)

        status_cb = QComboBox()
        status_cb.addItems(["all", "running", "completed", "failed",
                            "pending", "blocked", "paused"])
        status_cb.currentTextChanged.connect(self._on_status_changed)
        filter_bar.addWidget(status_cb)
        self._status_filter = status_cb

        filter_bar.addStretch()
        layout.addLayout(filter_bar)

        # Table view
        table = QTableView()
        table.setModel(self._model)
        table.setSortingEnabled(True)
        table.setSelectionBehavior(QTableView.SelectionBehavior.SelectRows)
        table.setSelectionMode(QTableView.SelectionMode.SingleSelection)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setDefaultSectionSize(24)

        # Stretch last section
        header = table.horizontalHeader()
        header.setStretchLastSection(True)
        header.setSectionResizeMode(QHeaderView.ResizeMode.Interactive)

        # Connect signals
        table.clicked.connect(self._on_clicked)
        table.doubleClicked.connect(self._on_double_clicked)

        layout.addWidget(table)
        self._table = table

        if self._parent:
            self._parent.layout().addWidget(container)

        self._container = container
        return container

    # ── Filter ────────────────────────────────────────────────────────

    def _on_search_changed(self, text: str) -> None:
        self._model.set_filter_text(text)

    def _on_status_changed(self, status: str) -> None:
        self._model.set_filter_status(status)

    # ── Selection ─────────────────────────────────────────────────────

    def _on_clicked(self, index: QModelIndex) -> None:
        if not self._on_selection:
            return
        row_data = self._model.get_row_data(index.row())
        if row_data:
            self._on_selection(row_data.mission_id)

    def _on_double_clicked(self, index: QModelIndex) -> None:
        if not self._on_double_click:
            return
        row_data = self._model.get_row_data(index.row())
        if row_data:
            self._on_double_click(row_data.mission_id)

    def on_selection(self, handler: Callable[[str], None]) -> None:
        self._on_selection = handler

    def on_double_click(self, handler: Callable[[str], None]) -> None:
        self._on_double_click = handler

    # ── Data ──────────────────────────────────────────────────────────

    def set_data(self, missions: List[Dict]) -> None:
        """Set mission data from DTO.

        Args:
            missions: List of dicts with keys: id, status, priority,
                      progress, owner, started_at, elapsed
        """
        data = []
        for m in missions:
            data.append(_MissionData(
                mission_id=str(m.get("id", m.get("mission_id", "?"))),
                status=str(m.get("status", "unknown")),
                priority=str(m.get("priority", "normal")),
                progress=str(m.get("progress", "0%")),
                owner=str(m.get("owner", "")),
                started=str(m.get("started_at", m.get("started", "")))[:19],
                elapsed=str(m.get("elapsed", "--")),
            ))
        self._model.set_data(data)

    def get_selected_mission_id(self) -> Optional[str]:
        """Get the mission ID of the currently selected row."""
        if not self._table:
            return None
        indexes = self._table.selectionModel().selectedRows()
        if not indexes:
            return None
        row_data = self._model.get_row_data(indexes[0].row())
        return row_data.mission_id if row_data else None

    # ── Access ────────────────────────────────────────────────────────

    @property
    def widget(self) -> Optional[QWidget]:
        return self._container

    @property
    def table(self) -> Optional[QTableView]:
        return self._table

    @property
    def row_count(self) -> int:
        return self._model.rowCount()

    def clear(self) -> None:
        self._model.set_data([])

    def summary(self) -> str:
        return f"MissionTableWidget: {self.row_count} missions, {self._model._filter_status} filter"
