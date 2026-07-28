"""MissionInspector — Mission detail inspector for SAM Desktop.

Tabbed panel: Overview, Timeline, Steps, Approvals, Audit,
Recovery, Trust, Performance.
All data from DTO via bridge pipeline. Read-only. No domain access.
"""

from __future__ import annotations

from typing import Optional, Dict, List, Any

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QTabWidget, QTextEdit, QTableWidget, QTableWidgetItem,
        QGroupBox, QFormLayout, QFrame, QHeaderView,
        QScrollArea, QSplitter, QPushButton,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont, QColor, QBrush
    HAS_QT = True
except ImportError:
    HAS_QT = False


class _InfoRow(QWidget):
    """A labeled key-value pair row."""

    def __init__(self, label: str, value: str = "--", parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 2, 0, 2)
        lbl = QLabel(f"<b>{label}:</b>")
        lbl.setFixedWidth(140)
        layout.addWidget(lbl)
        self._value = QLabel(value)
        self._value.setWordWrap(True)
        self._value.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
        layout.addWidget(self._value, 1)
        self.setLayout(layout)

    def set_value(self, text: str) -> None:
        self._value.setText(text)

    def set_color(self, color: str) -> None:
        self._value.setStyleSheet(f"color: {color};")


class _SectionHeader(QLabel):
    def __init__(self, text: str, parent=None):
        super().__init__(parent)
        self.setText(f"<h3>{text}</h3>")
        self.setStyleSheet("margin-top: 8px; border-bottom: 1px solid #ccc;")


class _KeyValueTable(QWidget):
    """A 2-column key-value table for structured data."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)

        self._table = QTableWidget()
        self._table.setColumnCount(2)
        self._table.setHorizontalHeaderLabels(["Key", "Value"])
        self._table.horizontalHeader().setStretchLastSection(True)
        self._table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.ResizeToContents)
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setSelectionMode(QTableWidget.SelectionMode.NoSelection)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)

        layout.addWidget(self._table)
        self.setLayout(layout)

    def set_data(self, data: Dict[str, str]) -> None:
        self._table.setRowCount(len(data))
        for i, (key, val) in enumerate(data.items()):
            self._table.setItem(i, 0, QTableWidgetItem(str(key)))
            val_item = QTableWidgetItem(str(val))
            val_item.setFlags(val_item.flags() | Qt.ItemFlag.ItemIsSelectable)
            self._table.setItem(i, 1, val_item)
        self._table.resizeRowsToContents()


class _StatusIndicator(QLabel):
    """Colored status badge."""

    STATUS_COLORS = {
        "running": "#00AA00",
        "active": "#00AA00",
        "completed": "#888888",
        "failed": "#FF4444",
        "pending": "#FFAA00",
        "blocked": "#FF0000",
        "paused": "#AAAAAA",
        "cancelled": "#888888",
    }

    def __init__(self, status: str = "unknown", parent=None):
        super().__init__(parent)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        color = self.STATUS_COLORS.get(status.lower(), "#888888")
        self.setText(f"<span style='color:{color};font-weight:bold;'>●</span> {status}")
        self.setStyleSheet(f"padding: 4px 8px; border-radius: 4px; font-size: 14px;")


# ── Tab Widgets ──────────────────────────────────────────────────────

class _OverviewTab(QWidget):
    """Mission overview tab — mission identity, status, owner, duration."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Status row
        self._status = _StatusIndicator()
        layout.addWidget(self._status)

        # Info section
        info_group = QGroupBox("Mission Info")
        info_layout = QFormLayout()
        info_group.setLayout(info_layout)

        self._fields = {}
        for field in ["ID", "Name", "Status", "Priority", "Owner",
                       "Started", "Elapsed", "Progress", "Deadline",
                       "Source", "Type", "Tags"]:
            row = QHBoxLayout()
            lbl = QLabel("--")
            lbl.setTextInteractionFlags(Qt.TextInteractionFlag.TextSelectableByMouse)
            self._fields[field] = lbl
            info_layout.addRow(f"{field}:", lbl)

        layout.addWidget(info_group)
        layout.addStretch()

    def update(self, data: Dict) -> None:
        self._status.set_status(str(data.get("status", "unknown")))
        for field, label in self._fields.items():
            val = data.get(field.lower().replace(" ", "_"))
            if val is None:
                val = data.get(field.lower())
            if val is None:
                val = data.get(field)
            label.setText(str(val) if val is not None else "--")


class _TimelineTab(QWidget):
    """Mission-specific timeline events."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("<b>Mission Timeline</b>")
        layout.addWidget(header)

        self._events = QTableWidget()
        self._events.setColumnCount(4)
        self._events.setHorizontalHeaderLabels(
            ["Time", "Event", "Severity", "Description"])
        self._events.horizontalHeader().setStretchLastSection(True)
        self._events.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._events.setAlternatingRowColors(True)
        self._events.verticalHeader().setVisible(False)
        layout.addWidget(self._events)

    def update(self, events: List[Dict]) -> None:
        self._events.setRowCount(len(events))
        for i, ev in enumerate(events):
            self._events.setItem(i, 0, QTableWidgetItem(
                str(ev.get("time", ev.get("timestamp", "")))))
            self._events.setItem(i, 1, QTableWidgetItem(
                str(ev.get("event", ev.get("type", "")))))
            self._events.setItem(i, 2, QTableWidgetItem(
                str(ev.get("severity", ev.get("level", "")))))
            self._events.setItem(i, 3, QTableWidgetItem(
                str(ev.get("description", ev.get("message", "")))))
        self._events.resizeRowsToContents()


class _StepsTab(QWidget):
    """Mission execution steps list."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("<b>Execution Steps</b>")
        layout.addWidget(header)

        self._steps = QTableWidget()
        self._steps.setColumnCount(5)
        self._steps.setHorizontalHeaderLabels(
            ["#", "Step", "Status", "Duration", "Detail"])
        self._steps.horizontalHeader().setStretchLastSection(True)
        self._steps.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._steps.setAlternatingRowColors(True)
        self._steps.verticalHeader().setVisible(False)
        layout.addWidget(self._steps)

    def update(self, steps: List[Dict]) -> None:
        self._steps.setRowCount(len(steps))
        for i, step in enumerate(steps):
            self._steps.setItem(i, 0, QTableWidgetItem(str(i + 1)))
            self._steps.setItem(i, 1, QTableWidgetItem(
                str(step.get("name", step.get("step", "")))))
            self._steps.setItem(i, 2, QTableWidgetItem(
                str(step.get("status", "pending"))))
            self._steps.setItem(i, 3, QTableWidgetItem(
                str(step.get("duration", "--"))))
            self._steps.setItem(i, 4, QTableWidgetItem(
                str(step.get("detail", step.get("description", "")))))
        self._steps.resizeRowsToContents()


class _ApprovalsTab(QWidget):
    """Mission approvals list."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("<b>Approvals</b>")
        layout.addWidget(header)

        self._approvals = QTableWidget()
        self._approvals.setColumnCount(5)
        self._approvals.setHorizontalHeaderLabels(
            ["Approval", "Status", "Approver", "Reason", "Timestamp"])
        self._approvals.horizontalHeader().setStretchLastSection(True)
        self._approvals.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._approvals.setAlternatingRowColors(True)
        self._approvals.verticalHeader().setVisible(False)
        layout.addWidget(self._approvals)

    def update(self, approvals: List[Dict]) -> None:
        self._approvals.setRowCount(len(approvals))
        for i, ap in enumerate(approvals):
            self._approvals.setItem(i, 0, QTableWidgetItem(
                str(ap.get("id", ap.get("approval_id", "")))))
            self._approvals.setItem(i, 1, QTableWidgetItem(
                str(ap.get("status", "pending"))))
            self._approvals.setItem(i, 2, QTableWidgetItem(
                str(ap.get("approver", ap.get("approved_by", "")))))
            self._approvals.setItem(i, 3, QTableWidgetItem(
                str(ap.get("reason", ap.get("note", "")))))
            self._approvals.setItem(i, 4, QTableWidgetItem(
                str(ap.get("timestamp", ap.get("created_at", "")))))
        self._approvals.resizeRowsToContents()


class _AuditTab(QWidget):
    """Audit trail for this mission."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("<b>Audit Trail</b>")
        layout.addWidget(header)

        self._audit = QTableWidget()
        self._audit.setColumnCount(4)
        self._audit.setHorizontalHeaderLabels(
            ["Timestamp", "Action", "Actor", "Detail"])
        self._audit.horizontalHeader().setStretchLastSection(True)
        self._audit.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._audit.setAlternatingRowColors(True)
        self._audit.verticalHeader().setVisible(False)
        layout.addWidget(self._audit)

    def update(self, records: List[Dict]) -> None:
        self._audit.setRowCount(len(records))
        for i, rec in enumerate(records):
            self._audit.setItem(i, 0, QTableWidgetItem(
                str(rec.get("timestamp", rec.get("time", "")))))
            self._audit.setItem(i, 1, QTableWidgetItem(
                str(rec.get("action", rec.get("event", "")))))
            self._audit.setItem(i, 2, QTableWidgetItem(
                str(rec.get("actor", rec.get("user", "")))))
            self._audit.setItem(i, 3, QTableWidgetItem(
                str(rec.get("detail", rec.get("description", "")))))
        self._audit.resizeRowsToContents()


class _RecoveryTab(QWidget):
    """Recvery/retry history for this mission."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("<b>Recovery & Retry History</b>")
        layout.addWidget(header)

        self._recovery = QTableWidget()
        self._recovery.setColumnCount(4)
        self._recovery.setHorizontalHeaderLabels(
            ["Attempt", "Strategy", "Status", "Timestamp"])
        self._recovery.horizontalHeader().setStretchLastSection(True)
        self._recovery.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._recovery.setAlternatingRowColors(True)
        self._recovery.verticalHeader().setVisible(False)
        layout.addWidget(self._recovery)

    def update(self, records: List[Dict]) -> None:
        self._recovery.setRowCount(len(records))
        for i, rec in enumerate(records):
            self._recovery.setItem(i, 0, QTableWidgetItem(
                str(rec.get("attempt", rec.get("retry", i + 1)))))
            self._recovery.setItem(i, 1, QTableWidgetItem(
                str(rec.get("strategy", rec.get("type", "")))))
            self._recovery.setItem(i, 2, QTableWidgetItem(
                str(rec.get("status", ""))))
            self._recovery.setItem(i, 3, QTableWidgetItem(
                str(rec.get("timestamp", rec.get("time", "")))))
        self._recovery.resizeRowsToContents()


class _TrustTab(QWidget):
    """Trust metrics for this mission."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("<b>Trust Metrics</b>")
        layout.addWidget(header)

        self._info = QTextEdit()
        self._info.setReadOnly(True)
        layout.addWidget(self._info)

    def update(self, data: Dict) -> None:
        lines = []
        for key, val in data.items():
            lines.append(f"{key}: {val}")
        self._info.setText("\n".join(lines) if lines else "No trust data")


class _PerformanceTab(QWidget):
    """Performance metrics for this mission."""

    def __init__(self, parent=None):
        if not HAS_QT:
            return
        super().__init__(parent)
        layout = QVBoxLayout()
        self.setLayout(layout)

        header = QLabel("<b>Performance Metrics</b>")
        layout.addWidget(header)

        self._perf = QTableWidget()
        self._perf.setColumnCount(3)
        self._perf.setHorizontalHeaderLabels(["Metric", "Value", "Status"])
        self._perf.horizontalHeader().setStretchLastSection(True)
        self._perf.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._perf.verticalHeader().setVisible(False)
        layout.addWidget(self._perf)

    def update(self, metrics: Dict) -> None:
        self._perf.setRowCount(len(metrics))
        for i, (key, val) in enumerate(metrics.items()):
            self._perf.setItem(i, 0, QTableWidgetItem(str(key)))
            val_str = str(val.get("value", val)) if isinstance(val, dict) else str(val)
            status = str(val.get("status", "")) if isinstance(val, dict) else ""
            self._perf.setItem(i, 1, QTableWidgetItem(val_str))
            self._perf.setItem(i, 2, QTableWidgetItem(status))
        self._perf.resizeRowsToContents()


# ── Main MissionInspector ────────────────────────────────────────────

class MissionInspector(QWidget):
    """Mission detail inspector with tabbed view.

    Tabs: Overview, Timeline, Steps, Approvals, Audit, Recovery,
          Trust, Performance.
    All data from DTO. Read-only. No domain access.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        super().__init__(parent)

        # Empty state
        self._mission_id: Optional[str] = None
        self._mission_data: Optional[Dict] = None

        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Header
        self._header = QLabel("<h2>Mission Inspector</h2>")
        layout.addWidget(self._header)

        # Subheader
        self._subheader = QLabel("Select a mission to inspect.")
        self._subheader.setStyleSheet("color: #888888; margin-bottom: 8px;")
        layout.addWidget(self._subheader)

        # Tab widget
        self._tabs = QTabWidget()
        self._tabs.setTabPosition(QTabWidget.TabPosition.North)

        self._overview = _OverviewTab()
        self._timeline_tab = _TimelineTab()
        self._steps_tab = _StepsTab()
        self._approvals_tab = _ApprovalsTab()
        self._audit_tab = _AuditTab()
        self._recovery_tab = _RecoveryTab()
        self._trust_tab = _TrustTab()
        self._performance_tab = _PerformanceTab()

        self._tabs.addTab(self._overview, "Overview")
        self._tabs.addTab(self._timeline_tab, "Timeline")
        self._tabs.addTab(self._steps_tab, "Steps")
        self._tabs.addTab(self._approvals_tab, "Approvals")
        self._tabs.addTab(self._audit_tab, "Audit")
        self._tabs.addTab(self._recovery_tab, "Recovery")
        self._tabs.addTab(self._trust_tab, "Trust")
        self._tabs.addTab(self._performance_tab, "Performance")

        layout.addWidget(self._tabs)

    # ── Data ─────────────────────────────────────────────────────────

    def show_mission(self, mission_id: str,
                     mission_data: Optional[Dict] = None,
                     extended: Optional[Dict] = None) -> None:
        """Display a mission's detail.

        Args:
            mission_id: The mission ID.
            mission_data: Basic mission DTO (overview fields).
            extended: Extended data with keys:
                timeline (list), steps (list), approvals (list),
                audit (list), recovery (list), trust (dict),
                performance (dict).
        """
        self._mission_id = mission_id
        self._mission_data = mission_data or {}

        ext = extended or {}

        # Header
        name = mission_data.get("name", mission_data.get("title", mission_id))
        self._header.setText(f"<h2>Mission: {name}</h2>")
        self._subheader.setText(f"Inspecting <b>{mission_id}</b>")

        # Update tabs
        self._overview.update(mission_data or {})
        self._timeline_tab.update(ext.get("timeline", ext.get("events", [])))
        self._steps_tab.update(ext.get("steps", []))
        self._approvals_tab.update(ext.get("approvals", []))
        self._audit_tab.update(ext.get("audit", []))
        self._recovery_tab.update(ext.get("recovery", ext.get("retries", [])))
        self._trust_tab.update(ext.get("trust", ext.get("trust_data", {})))
        self._performance_tab.update(
            ext.get("performance", ext.get("metrics", {})))

        # Switch to overview
        self._tabs.setCurrentIndex(0)

    def clear(self) -> None:
        """Reset to empty state."""
        self._mission_id = None
        self._mission_data = None
        self._header.setText("<h2>Mission Inspector</h2>")
        self._subheader.setText("Select a mission to inspect.")

        self._overview.update({})
        self._timeline_tab.update([])
        self._steps_tab.update([])
        self._approvals_tab.update([])
        self._audit_tab.update([])
        self._recovery_tab.update([])
        self._trust_tab.update({})
        self._performance_tab.update({})

    @property
    def current_mission_id(self) -> Optional[str]:
        return self._mission_id

    @property
    def has_mission(self) -> bool:
        return self._mission_id is not None

    def summary(self) -> str:
        if self._mission_id:
            return f"MissionInspector: showing {self._mission_id}"
        return "MissionInspector: empty"
