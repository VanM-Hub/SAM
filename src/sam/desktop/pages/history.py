from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QLineEdit, QComboBox,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ...experience.models.history import HistoryEntry, HistoryEntrySeverity
from ...operations.engine.history import HistoryEngine
from ...telemetry.service import TelemetryService


class HistoryPage(QWidget):
    """Halaman History untuk Desktop."""

    def __init__(self, telemetry):
        super().__init__()
        self.telemetry = telemetry
        self.history_engine = HistoryEngine(telemetry)
        self.current_history = []
        self._init_ui()
        self._start_refresh()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("\U0001f4dc History")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0e0;")
        header.addWidget(title)
        header.addStretch()

        # Filter
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("\U0001f50d Search...")
        self.filter_input.setStyleSheet("""
            QLineEdit {
                background: #12121a;
                border: 1px solid #2a2a3a;
                border-radius: 6px;
                padding: 6px 12px;
                color: #e0e0e0;
                min-width: 200px;
            }
        """)
        self.filter_input.textChanged.connect(self._apply_filters)
        header.addWidget(self.filter_input)

        self.severity_combo = QComboBox()
        self.severity_combo.addItems(["All", "info", "success", "warning", "error", "critical"])
        self.severity_combo.setStyleSheet("""
            QComboBox {
                background: #12121a;
                border: 1px solid #2a2a3a;
                border-radius: 6px;
                padding: 4px 8px;
                color: #e0e0e0;
            }
        """)
        self.severity_combo.currentTextChanged.connect(self._apply_filters)
        header.addWidget(self.severity_combo)

        refresh_btn = QPushButton("\U0001f504 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #2a4a6a;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                color: #fff;
            }
            QPushButton:hover { background: #3a5a7a; }
        """)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)

        layout.addLayout(header)

        # History list
        self.history_list = QListWidget()
        self.history_list.setStyleSheet("""
            QListWidget {
                background: #0a0a0f;
                border: 1px solid #2a2a3a;
                border-radius: 8px;
                padding: 4px;
            }
            QListWidget::item {
                padding: 10px 14px;
                border-bottom: 1px solid #1a1a2a;
                border-radius: 4px;
            }
            QListWidget::item:hover {
                background: #12121a;
            }
        """)
        layout.addWidget(self.history_list)

        self.setLayout(layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(10000)

    def _start_refresh(self):
        self.refresh()

    def refresh(self):
        try:
            entries = self.history_engine.get_timeline(limit=100)
            self.current_history = entries
            self._render(entries)
        except Exception as e:
            self._render_error(str(e))

    def _apply_filters(self):
        self.refresh()

    def _render(self, entries):
        self.history_list.clear()

        if not entries:
            item = QListWidgetItem("No history found.")
            item.setForeground(QColor("#888"))
            self.history_list.addItem(item)
            return

        for entry in entries:
            colors = {
                "info": "#a0a0b0",
                "success": "#4ae04a",
                "warning": "#e0c06a",
                "error": "#e06a6a",
                "critical": "#ff4444",
            }
            time_str = entry.timestamp.strftime("%H:%M:%S")
            date_str = entry.timestamp.strftime("%Y-%m-%d")
            text = "{} {}  {}".format(date_str, time_str, entry.title)

            # Truncate if too long
            if len(text) > 120:
                text = text[:117] + "..."

            item = QListWidgetItem(text)
            item.setForeground(QColor(colors.get(entry.severity.value, "#a0a0b0")))
            item.setData(Qt.UserRole, entry)
            self.history_list.addItem(item)

    def _render_error(self, error):
        self.history_list.clear()
        item = QListWidgetItem("\u26a0\ufe0f Error loading history: {}".format(error))
        item.setForeground(QColor("#e06a6a"))
        self.history_list.addItem(item)
