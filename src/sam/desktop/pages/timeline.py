from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QComboBox, QListWidget, QListWidgetItem,
    QScrollArea, QFrame
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ...experience.timeline import TimelineBuilder
from ...experience.models.timeline import TimelineModel, ActivityItem, ActivitySeverity
from ...telemetry.service import TelemetryService


class TimelinePage(QWidget):
    """Halaman Timeline untuk Desktop Operations Console."""

    def __init__(self, telemetry):
        super().__init__()
        self.telemetry = telemetry
        self.builder = TimelineBuilder(telemetry)
        self.current_model = None
        self._init_ui()
        self._start_refresh()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("\U0001f4cb Activity Timeline")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0e0;")
        header.addWidget(title)
        header.addStretch()

        # Filter input
        self.filter_input = QLineEdit()
        self.filter_input.setPlaceholderText("\U0001f50d Filter activities...")
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

        # Severity combo
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

        # Timeline list
        self.timeline_list = QListWidget()
        self.timeline_list.setStyleSheet("""
            QListWidget {
                background: #0a0a0f;
                border: none;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
                border-bottom: 1px solid #1a1a2a;
                border-radius: 4px;
                margin: 2px 0;
            }
            QListWidget::item:hover {
                background: #12121a;
            }
        """)
        layout.addWidget(self.timeline_list)

        self.setLayout(layout)

        # Timer refresh setiap 10 detik
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(10000)

    def _start_refresh(self):
        """Mulai refresh pertama."""
        self.refresh()

    def refresh(self):
        """Refresh timeline."""
        try:
            # Build dengan filter yang aktif
            filters = None
            severity_text = self.severity_combo.currentText()
            if severity_text != "All":
                from ...experience.models.timeline import TimelineFilter, ActivitySeverity
                filters = TimelineFilter(severities=[ActivitySeverity(severity_text)])

            model = self.builder.build(filters)
            self.current_model = model
            self._render(model)
        except Exception as e:
            self._render_error(str(e))

    def _apply_filters(self):
        """Apply filters and refresh."""
        self.refresh()

    def _render(self, model):
        """Render TimelineModel ke UI."""
        self.timeline_list.clear()

        if not model.activities:
            item = QListWidgetItem("No activities found.")
            item.setForeground(QColor("#888"))
            self.timeline_list.addItem(item)
            return

        for activity in model.activities:
            item = QListWidgetItem(self._format_activity(activity))
            item.setData(Qt.UserRole, activity)

            # Warna berdasarkan severity
            colors = {
                "info": "#a0a0b0",
                "success": "#4ae04a",
                "warning": "#e0c06a",
                "error": "#e06a6a",
                "critical": "#ff4444",
            }
            item.setForeground(QColor(colors.get(activity.severity.value, "#a0a0b0")))

            self.timeline_list.addItem(item)

        # Info jumlah
        info_item = QListWidgetItem("{} activities".format(len(model.activities)))
        info_item.setForeground(QColor("#666"))
        self.timeline_list.addItem(info_item)

    def _format_activity(self, activity):
        """Format aktivitas menjadi teks."""
        time_str = activity.timestamp.strftime("%H:%M:%S")
        duration = " ({:.0f}ms)".format(activity.duration_ms) if activity.duration_ms else ""
        return "{}  {}{}".format(time_str, activity.title, duration)

    def _render_error(self, error):
        """Tampilkan error di UI."""
        self.timeline_list.clear()
        item = QListWidgetItem("\u26a0\ufe0f Error loading timeline: {}".format(error))
        item.setForeground(QColor("#e06a6a"))
        self.timeline_list.addItem(item)
