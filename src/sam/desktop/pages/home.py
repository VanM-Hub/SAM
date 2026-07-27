from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QGridLayout,
    QFrame, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor, QPalette

from ...experience.builder import ExperienceBuilder
from ...experience.pages.home import HomeModel, HomeStatus


class HomePage(QWidget):
    """Halaman Home untuk Desktop Operations Console."""

    def __init__(self, builder: ExperienceBuilder):
        super().__init__()
        self.builder = builder
        self.current_model = None
        self._init_ui()
        self._start_refresh()

    def _init_ui(self):
        """Initialize UI components."""
        layout = QVBoxLayout()
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setSpacing(16)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)

        self.setLayout(layout)

        # Timer untuk refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)  # 5 detik

    def _start_refresh(self):
        """Mulai refresh (dipanggil di __init__)."""
        self.refresh()

    def refresh(self):
        """Refresh tampilan dari Experience Builder."""
        try:
            model = self.builder.build_home()
            self.current_model = model
            self._render(model)
        except Exception as e:
            self._render_error(str(e))

    def _render(self, model: HomeModel):
        """Render HomeModel ke UI."""
        # Bersihkan layout
        self._clear_layout(self.content_layout)

        # 1. Header — Salam dan Status
        header = QHBoxLayout()
        greeting = QLabel("Good {}.".format('morning' if 8 < 12 else 'afternoon'))
        greeting.setStyleSheet("font-size: 24px; font-weight: bold; color: #e0e0e0;")
        status_label = QLabel(self._status_text(model.status))
        status_label.setStyleSheet(self._status_style(model.status))
        header.addWidget(greeting)
        header.addStretch()
        header.addWidget(status_label)
        self.content_layout.addLayout(header)

        # 2. Stat Grid — 3 kolom
        grid = QGridLayout()
        grid.setSpacing(16)

        # System Health
        health_box = self._stat_box("System Health", "{:.0f}%".format(model.system_health))
        grid.addWidget(health_box, 0, 0)

        # Mission Health
        mission_box = self._stat_box("Mission Health", "{:.0f}%".format(model.mission_health))
        grid.addWidget(mission_box, 0, 1)

        # Uptime
        uptime_box = self._stat_box("Uptime", model.uptime)
        grid.addWidget(uptime_box, 0, 2)

        self.content_layout.addLayout(grid)

        # 3. Recent Activity
        activity_label = QLabel("Recent Activity")
        activity_label.setStyleSheet(
            "font-size: 16px; font-weight: bold; color: #c0c0c0; margin-top: 8px;"
        )
        self.content_layout.addWidget(activity_label)

        for change in model.recent_changes[:5]:
            change_widget = QLabel(change["message"])
            change_widget.setStyleSheet(
                "padding: 6px 12px; background: #1a1a2a; border-radius: 4px; color: #a0a0b0;"
            )
            self.content_layout.addWidget(change_widget)

        # 4. Recommendations / Attention
        if model.needs_attention:
            attention_label = QLabel("\u26a0\ufe0f Needs Attention")
            attention_label.setStyleSheet(
                "font-size: 16px; font-weight: bold; color: #e0c06a; margin-top: 8px;"
            )
            self.content_layout.addWidget(attention_label)

            if model.pending_approvals > 0:
                self.content_layout.addWidget(
                    QLabel("\U0001f4cb {} pending approvals".format(model.pending_approvals))
                )
            if model.pending_tasks > 0:
                self.content_layout.addWidget(
                    QLabel("\U0001f4cc {} pending tasks".format(model.pending_tasks))
                )
            if model.recommendations:
                for rec in model.recommendations[:3]:
                    rec_widget = QLabel("\U0001f4a1 {}".format(rec))
                    rec_widget.setStyleSheet(
                        "padding: 6px 12px; background: #1a2a3a; border-radius: 4px; color: #6aaae0;"
                    )
                    self.content_layout.addWidget(rec_widget)

    def _clear_layout(self, layout):
        """Hapus semua widget dari layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _stat_box(self, label: str, value: str):
        """Buat box statistik."""
        widget = QFrame()
        widget.setStyleSheet("""
            QFrame {
                background: #12121a;
                border: 1px solid #2a2a3a;
                border-radius: 8px;
                padding: 12px;
            }
        """)
        layout = QVBoxLayout()
        label_widget = QLabel(label)
        label_widget.setStyleSheet(
            "color: #888; font-size: 12px; letter-spacing: 0.5px;"
        )
        value_widget = QLabel(value)
        value_widget.setStyleSheet(
            "color: #e0e0e0; font-size: 28px; font-weight: 600;"
        )
        layout.addWidget(label_widget)
        layout.addWidget(value_widget)
        widget.setLayout(layout)
        return widget

    def _status_text(self, status: HomeStatus) -> str:
        """Status manusia."""
        mapping = {
            HomeStatus.HEALTHY: "\u2705 Healthy",
            HomeStatus.BUSY: "\U0001f504 Busy",
            HomeStatus.RECOVERING: "\U0001f527 Recovering",
            HomeStatus.LEARNING: "\U0001f9e0 Learning",
            HomeStatus.STARTING: "\U0001f680 Starting",
            HomeStatus.STOPPING: "\u23f9\ufe0f Stopping",
            HomeStatus.DEGRADED: "\u26a0\ufe0f Degraded",
            HomeStatus.UNHEALTHY: "\u274c Unhealthy",
        }
        return mapping.get(status, "\u2753 Unknown")

    def _status_style(self, status: HomeStatus) -> str:
        """CSS style untuk status."""
        styles = {
            HomeStatus.HEALTHY: "color: #4ae04a; font-weight: bold; font-size: 18px;",
            HomeStatus.BUSY: "color: #e0c06a; font-weight: bold; font-size: 18px;",
            HomeStatus.RECOVERING: "color: #e09a6a; font-weight: bold; font-size: 18px;",
            HomeStatus.LEARNING: "color: #6aaae0; font-weight: bold; font-size: 18px;",
            HomeStatus.STARTING: "color: #6aaae0; font-weight: bold; font-size: 18px;",
            HomeStatus.STOPPING: "color: #e06a6a; font-weight: bold; font-size: 18px;",
            HomeStatus.DEGRADED: "color: #e0c06a; font-weight: bold; font-size: 18px;",
            HomeStatus.UNHEALTHY: "color: #e06a6a; font-weight: bold; font-size: 18px;",
        }
        return styles.get(status, "color: #a0a0b0; font-weight: bold; font-size: 18px;")

    def _render_error(self, error: str):
        """Tampilkan error di UI."""
        self._clear_layout(self.content_layout)
        error_label = QLabel("\u26a0\ufe0f Error loading Home: {}".format(error))
        error_label.setStyleSheet("color: #e06a6a; font-size: 14px; padding: 16px;")
        self.content_layout.addWidget(error_label)
