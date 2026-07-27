"""
Work Page v3.1 — Narrative Work Center.

Setiap pekerjaan punya cerita, bukan status update.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt, QTimer

from ...experience.engine import ExperienceEngine


class WorkPage(QWidget):
    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setStyleSheet("background: transparent; padding: 24px 24px 8px 24px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Work")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)
        sub = QLabel("What SAM is working on.")
        sub.setStyleSheet("color: #606070; font-size: 12px; margin-top: 2px;")
        h_layout.addWidget(sub)
        root.addWidget(header)

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
            narratives = self.experience.build_narrative_work()
            self._render(model, narratives)
        except Exception:
            pass

    def _render(self, model, narratives):
        self._clear()

        if not model.items:
            # Narrative empty state
            empty = QFrame()
            empty.setStyleSheet("""
                QFrame {
                    background: #0a0a12;
                    border: 1px solid #1a3a1a;
                    border-radius: 10px;
                    padding: 32px;
                }
            """)
            e_layout = QVBoxLayout(empty)
            e_layout.setAlignment(Qt.AlignCenter)
            e_label = QLabel("\u2705  No active work")
            e_label.setStyleSheet("color: #4ae04a; font-size: 18px;")
            e_layout.addWidget(e_label)
            e_sub = QLabel("All tasks are completed. Nothing requires your attention.")
            e_sub.setStyleSheet("color: #606070; font-size: 13px;")
            e_layout.addWidget(e_sub)
            self._layout.addWidget(empty)

            # Show narratives instead
            for n in narratives:
                card = self._narrative_card(n)
                self._layout.addWidget(card)

            self._layout.addStretch()
            return

        for item in model.items[:10]:
            border_map = {
                "failed": "#3a1a1a",
                "running": "#1a2a3a",
                "Review required": "#3a3a1a",
                "completed": "#1a3a1a",
            }
            badge_map = {
                "failed": "#e06a6a",
                "running": "#6aaae0",
                "Review required": "#e0c06a",
                "completed": "#4ae04a",
            }

            border = border_map.get(item.status, "#1a1a2a")
            badge_color = badge_map.get(item.status, "#808090")

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

            # Title + badge
            header_row = QHBoxLayout()
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

            # Progress
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
                prog_label.setStyleSheet("color: #707080; font-size: 11px;")
                card_layout.addWidget(prog_label)

            # Approval — narrative
            if item.approval_needed:
                approve_frame = QFrame()
                approve_frame.setStyleSheet("""
                    QFrame {
                        background: #1a1a0a;
                        border: 1px solid #3a3a1a;
                        border-radius: 6px;
                        padding: 8px 12px;
                    }
                """)
                a_layout = QVBoxLayout(approve_frame)
                a_layout.setSpacing(4)

                req = QLabel("\u26a0\ufe0f  SAM is waiting for your approval.")
                req.setStyleSheet("color: #e0c06a; font-size: 12px; font-weight: bold;")
                a_layout.addWidget(req)

                if item.approval_reason:
                    reason = QLabel("Reason: {}".format(item.approval_reason))
                    reason.setStyleSheet("color: #707080; font-size: 11px;")
                    a_layout.addWidget(reason)

                est = QLabel("Estimated review time: 2 minutes.")
                est.setStyleSheet("color: #707080; font-size: 11px;")
                a_layout.addWidget(est)

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
                """)
                approve_btn.setFixedWidth(120)
                a_layout.addWidget(approve_btn)

                card_layout.addWidget(approve_frame)

            self._layout.addWidget(card)

        # Narrative cards
        for n in narratives:
            card = self._narrative_card(n)
            self._layout.addWidget(card)

        self._layout.addStretch()

    def _narrative_card(self, n):
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #0a0a12;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 10px 14px;
                margin-top: 4px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(2)

        title = QLabel(n.title)
        title.setStyleSheet("color: #c0c0d0; font-size: 13px; font-weight: 500;")
        title.setWordWrap(True)
        c_layout.addWidget(title)

        if n.details:
            d = QLabel(n.details)
            d.setStyleSheet("color: #707080; font-size: 11px;")
            d.setWordWrap(True)
            c_layout.addWidget(d)

        return card

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
