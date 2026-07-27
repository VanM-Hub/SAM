"""
Work Page — Pekerjaan aktif dengan progress dan approval.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ...experience.engine import ExperienceEngine


class WorkPage(QWidget):
    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Work")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0; margin-bottom: 8px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(12)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)
        self.refresh()

    def refresh(self):
        try:
            model = self.experience.build_work()
            self._render(model)
        except Exception:
            pass

    def _render(self, model):
        self._clear()

        if not model.items:
            empty = QLabel("No active work.")
            empty.setStyleSheet("color: #606070; font-size: 14px; padding: 24px;")
            self.content_layout.addWidget(empty)
            return

        for item in model.items[:5]:
            # Card
            card = QFrame()
            status_color = "#4ae04a"
            if item.status == "failed":
                status_color = "#e06a6a"
            elif item.status == "running":
                status_color = "#6aaae0"
            elif item.status == "Review required":
                status_color = "#e0c06a"

            card.setStyleSheet("""
                QFrame {
                    background: #0d0d16;
                    border: 1px solid #1a1a2a;
                    border-radius: 8px;
                    padding: 12px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(8)

            # Title + Status
            header = QHBoxLayout()
            title_label = QLabel(item.title)
            title_label.setStyleSheet("color: #e0e0e0; font-size: 16px; font-weight: bold;")
            header.addWidget(title_label)
            header.addStretch()
            status_label = QLabel(item.status)
            status_label.setStyleSheet("color: {}; font-size: 12px;".format(status_color))
            header.addWidget(status_label)
            card_layout.addLayout(header)

            # Progress bar
            if item.progress:
                progress = QProgressBar()
                progress.setValue(item.progress.percent)
                progress.setFixedHeight(8)
                progress.setStyleSheet("""
                    QProgressBar {
                        background: #1a1a2a;
                        border: none;
                        border-radius: 4px;
                    }
                    QProgressBar::chunk {
                        background: #2a6a4a;
                        border-radius: 4px;
                    }
                """)
                card_layout.addWidget(progress)

                progress_text = "Step {} of {} — {}".format(
                    item.progress.current_step, item.progress.total_steps,
                    item.progress.estimated_remaining or "{}%".format(item.progress.percent),
                )
                prog_label = QLabel(progress_text)
                prog_label.setStyleSheet("color: #808090; font-size: 11px;")
                card_layout.addWidget(prog_label)

            # Approval
            if item.approval_needed:
                approve = QPushButton("\u2705  Review & Approve")
                approve.setStyleSheet("""
                    QPushButton {
                        background: #2a5a3a;
                        border: none;
                        border-radius: 6px;
                        padding: 8px 16px;
                        color: #fff;
                        font-size: 12px;
                    }
                    QPushButton:hover { background: #3a7a4a; }
                """)
                card_layout.addWidget(approve)

                if item.approval_reason:
                    reason = QLabel("Reason: {}".format(item.approval_reason))
                    reason.setStyleSheet("color: #606070; font-size: 11px;")
                    card_layout.addWidget(reason)

            self.content_layout.addWidget(card)

    def _clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
