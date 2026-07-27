"""
Home Page — Ringkasan operasional.

Apakah sistem sehat? Apa yang terjadi? Perlu tindakan?
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ...experience.engine import ExperienceEngine, HomeExperience, SystemStatus


class HomePage(QWidget):
    """Halaman Home — dapat dibaca < 5 detik."""

    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(20)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)

        # --- Widget containers ---
        self.status_card = QLabel("SAM is Healthy")
        self.detail_card = QLabel("Everything is operating normally.")
        self.purpose_label = QLabel("")
        self.activity_label = QLabel("")
        self.attention_label = QLabel("No action required")
        self.rec_label = QLabel("")

        # Build structure
        self._build_structure()

        scroll.setWidget(self.content)
        layout.addWidget(scroll)
        self.setLayout(layout)

        # Refresh
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)
        self.refresh()

    def _build_structure(self):
        # 1. Status — big card
        self.status_label = QLabel()
        font = QFont()
        font.setPointSize(20)
        font.setBold(True)
        self.status_label.setFont(font)
        self.status_label.setStyleSheet("color: #4ae04a; padding: 0;")
        self.content_layout.addWidget(self.status_label)

        self.detail_label = QLabel()
        self.detail_label.setStyleSheet("color: #a0a0b0; font-size: 14px; padding: 0 0 8px 0;")
        self.detail_label.setWordWrap(True)
        self.content_layout.addWidget(self.detail_label)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #1a1a2a;")
        self.content_layout.addWidget(sep)

        # 2. Purpose
        purpose_title = QLabel("Purpose")
        purpose_title.setStyleSheet("color: #808090; font-size: 11px; text-transform: uppercase; letter-spacing: 1px;")
        self.content_layout.addWidget(purpose_title)
        self.purpose_label.setStyleSheet("color: #e0e0e0; font-size: 15px;")
        self.content_layout.addWidget(self.purpose_label)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.HLine)
        sep2.setStyleSheet("color: #1a1a2a;")
        self.content_layout.addWidget(sep2)

        # 3. Current Activity
        activity_title = QLabel("Current Activity")
        activity_title.setStyleSheet("color: #808090; font-size: 11px; letter-spacing: 1px;")
        self.content_layout.addWidget(activity_title)
        self.activity_label.setStyleSheet("color: #c0c0c0; font-size: 14px;")
        self.activity_label.setWordWrap(True)
        self.content_layout.addWidget(self.activity_label)

        # Separator
        sep3 = QFrame()
        sep3.setFrameShape(QFrame.HLine)
        sep3.setStyleSheet("color: #1a1a2a;")
        self.content_layout.addWidget(sep3)

        # 4. Attention
        attention_title = QLabel("Attention")
        attention_title.setStyleSheet("color: #808090; font-size: 11px; letter-spacing: 1px;")
        self.content_layout.addWidget(attention_title)
        self.attention_label.setStyleSheet("color: #4ae04a; font-size: 14px;")
        self.attention_label.setWordWrap(True)
        self.content_layout.addWidget(self.attention_label)

        # Separator
        sep4 = QFrame()
        sep4.setFrameShape(QFrame.HLine)
        sep4.setStyleSheet("color: #1a1a2a;")
        self.content_layout.addWidget(sep4)

        # 5. Recommendations
        rec_title = QLabel("Recommendations")
        rec_title.setStyleSheet("color: #808090; font-size: 11px; letter-spacing: 1px;")
        self.content_layout.addWidget(rec_title)
        self.rec_label.setStyleSheet("color: #6aaae0; font-size: 13px;")
        self.rec_label.setWordWrap(True)
        self.content_layout.addWidget(self.rec_label)

        # Spacer
        self.content_layout.addStretch()

    def refresh(self):
        try:
            model = self.experience.build_home()
            self._render(model)
        except Exception as e:
            self.status_label.setText("Error loading Home")
            self.detail_label.setText(str(e))

    def _render(self, model):
        # Status
        if model.health.status == SystemStatus.HEALTHY:
            color = "#4ae04a"
            icon = "\u2705"
        elif model.health.status == SystemStatus.PROBLEM:
            color = "#e06a6a"
            icon = "\u274c"
        elif model.health.status == SystemStatus.RECOVERING:
            color = "#e0c06a"
            icon = "\U0001f504"
        else:
            color = "#6aaae0"
            icon = "\U0001f9e0"

        self.status_label.setText("{}  {}".format(icon, model.health.message))
        self.status_label.setStyleSheet("color: {}; font-size: 20px; font-weight: bold; padding: 0;".format(color))

        self.detail_label.setText(model.health.detail)

        # Purpose
        self.purpose_label.setText("\U0001f3af  {}".format(model.purpose.name))

        # Current activity
        self.activity_label.setText(model.current_activity.title)
        if model.current_activity.activity_log:
            log_text = ""
            for item in model.current_activity.activity_log[:3]:
                log_text += "{}  {}\n".format(item.time, item.description)
            self.activity_label.setText(log_text.strip())

        # Attention
        if model.attention.needs_attention:
            self.attention_label.setStyleSheet("color: #e0c06a; font-size: 14px;")
            text = "\u26a0\ufe0f  {}".format(model.attention.message)
            if model.attention.reason:
                text += "\n    Reason: {}".format(model.attention.reason)
            self.attention_label.setText(text)
        else:
            self.attention_label.setStyleSheet("color: #4ae04a; font-size: 14px;")
            self.attention_label.setText("\u2705  {}".format(model.attention.message))

        # Recommendations
        recs = []
        for r in model.recommendations:
            recs.append(r.message)
        self.rec_label.setText("\n".join(recs))
