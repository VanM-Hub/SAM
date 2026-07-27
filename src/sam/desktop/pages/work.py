"""
Work Page v3.1 — Work Center.

Daftar pekerjaan aktif.
Progress bar.
Approval.
ETA.
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
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: transparent; padding: 24px 24px 8px 24px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Work")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)
        root.addWidget(header)

        # Scroll
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                width: 4px;
                background: transparent;
            }
            QScrollBar::handle:vertical {
                background: #2a2a3a;
                border-radius: 2px;
            }
        """)

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self.content)
        self._layout.setContentsMargins(24, 8, 24, 32)
        self._layout.setSpacing(12)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

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
            empty = QFrame()
            empty.setStyleSheet("""
                QFrame {
                    background: #0a0a12;
                    border: 1px solid #1a1a2a;
                    border-radius: 10px;
                    padding: 32px;
                }
            """)
            e_layout = QVBoxLayout(empty)
            e_layout.setAlignment(Qt.AlignCenter)
            e_label = QLabel("\u2705  No active work")
            e_label.setStyleSheet("color: #4ae04a; font-size: 16px;")
            e_layout.addWidget(e_label)
            e_sub = QLabel("All tasks are completed.")
            e_sub.setStyleSheet("color: #606070; font-size: 12px;")
            e_layout.addWidget(e_sub)
            self._layout.addWidget(empty)
            self._layout.addStretch()
            return

        for item in model.items[:10]:
            # Status color
            if item.status == "failed":
                border = "#3a1a1a"
                badge_color = "#e06a6a"
            elif item.status == "running":
                border = "#1a2a3a"
                badge_color = "#6aaae0"
            elif item.status == "Review required":
                border = "#3a3a1a"
                badge_color = "#e0c06a"
            elif item.status == "completed":
                border = "#1a3a1a"
                badge_color = "#4ae04a"
            else:
                border = "#1a1a2a"
                badge_color = "#808090"

            card = QFrame()
            card.setStyleSheet("""
                QFrame {{
                    background: #0a0a12;
                    border: 1px solid {};
                    border-radius: 10px;
                    padding: 16px;
                }}
            """.format(border))
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(10)

            # Row 1: Title + badge
            header_row = QHBoxLayout()
            header_row.setSpacing(8)

            title_label = QLabel(item.title)
            title_label.setStyleSheet("color: #e0e0e0; font-size: 16px; font-weight: bold;")
            header_row.addWidget(title_label)
            header_row.addStretch()

            badge = QLabel(item.status)
            badge.setStyleSheet("""
                color: {};
                background: #0d0d18;
                border: 1px solid {};
                border-radius: 4px;
                padding: 2px 8px;
                font-size: 11px;
                font-weight: 500;
            """.format(badge_color, border))
            header_row.addWidget(badge)

            card_layout.addLayout(header_row)

            # Progress bar
            if item.progress:
                prog_bar = QProgressBar()
                prog_bar.setValue(item.progress.percent)
                prog_bar.setFixedHeight(6)
                prog_bar.setTextVisible(False)
                prog_bar.setStyleSheet("""
                    QProgressBar {
                        background: #1a1a2a;
                        border: none;
                        border-radius: 3px;
                    }
                    QProgressBar::chunk {
                        background: #2a6a4a;
                        border-radius: 3px;
                    }
                """)
                card_layout.addWidget(prog_bar)

                prog_text = "Step {} of {}  —  {}".format(
                    item.progress.current_step,
                    item.progress.total_steps,
                    item.progress.estimated_remaining or "{}% complete".format(item.progress.percent),
                )
                prog_label = QLabel(prog_text)
                prog_label.setStyleSheet("color: #808090; font-size: 11px;")
                card_layout.addWidget(prog_label)

            # Approval
            if item.approval_needed:
                approve_frame = QFrame()
                approve_frame.setStyleSheet("""
                    QFrame {
                        background: #1a1a0a;
                        border: 1px solid #3a3a1a;
                        border-radius: 6px;
                        padding: 8px 12px;
                        margin-top: 4px;
                    }
                """)
                a_layout = QVBoxLayout(approve_frame)
                a_layout.setSpacing(4)

                req_label = QLabel("\u26a0\ufe0f  Review required")
                req_label.setStyleSheet("color: #e0c06a; font-size: 12px; font-weight: bold;")
                a_layout.addWidget(req_label)

                if item.approval_reason:
                    reason = QLabel("Reason: {}".format(item.approval_reason))
                    reason.setStyleSheet("color: #808090; font-size: 11px;")
                    a_layout.addWidget(reason)

                approve_btn = QPushButton("  \u2705  Approve")
                approve_btn.setCursor(Qt.PointingHandCursor)
                approve_btn.setStyleSheet("""
                    QPushButton {
                        background: #2a5a3a;
                        border: none;
                        border-radius: 6px;
                        padding: 6px 14px;
                        color: #fff;
                        font-size: 12px;
                        font-weight: 500;
                    }
                    QPushButton:hover {
                        background: #3a7a4a;
                    }
                    QPushButton:pressed {
                        background: #1a4a2a;
                    }
                """)
                approve_btn.setFixedWidth(120)
                a_layout.addWidget(approve_btn)

                card_layout.addWidget(approve_frame)

            self._layout.addWidget(card)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
