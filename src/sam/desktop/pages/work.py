"""
Work Page v4.0 — Conversation-powered.

'What is SAM doing?'
Menggunakan Conversation.answer() + Conversation.recommendations().
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QProgressBar, QPushButton, QScrollArea,
)
from PySide6.QtCore import Qt, QTimer

from ...operations.conversation_api import Conversation
from ..widgets import StatusCard


class WorkPage(QWidget):
    """Work — 'What is SAM doing?' — dari Conversation."""

    def __init__(self, conversation: Conversation):
        super().__init__()
        self.conversation = conversation
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
        sub.setStyleSheet("color: #606070; font-size: 12px;")
        h_layout.addWidget(sub)
        root.addWidget(header)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setStyleSheet("""
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical { width: 4px; background: transparent; }
            QScrollBar::handle:vertical { background: #2a2a3a; border-radius: 2px; }
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

    def update_context(self, ctx):
        pass

    def refresh(self):
        try:
            # ================================================================
            # DARI Conversation — answer() + recommendations()
            # ================================================================
            overview = self.conversation.answer("What's happening?")
            recs = self.conversation.recommendations()
            self._render(overview, recs)
        except Exception:
            pass

    def _render(self, overview, recs):
        self._clear()

        items = []

        # SAM action sebagai item utama
        if overview.sam_action:
            items.append({
                "title": overview.sam_action,
                "status": "running" if "monitoring" in overview.sam_action.lower() else "active",
                "description": overview.summary or "",
                "badge": "Active",
                "badge_color": "#6aaae0",
            })

        # Recommendations sebagai work items
        if recs.recommendations:
            for r in recs.recommendations[:5]:
                items.append({
                    "title": r,
                    "status": "pending",
                    "description": "",
                    "badge": "Recommendation",
                    "badge_color": "#e0c06a",
                })

        if not items:
            empty = QFrame()
            empty.setStyleSheet("""
                QFrame { background: #0a0a12; border: 1px solid #1a3a1a;
                         border-radius: 10px; padding: 32px; }
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
            self._layout.addStretch()
            return

        for item in items[:10]:
            badge_color = item.get("badge_color", "#808090")
            border_color = self._border_from(item.get("badge_color", "#808090"))

            card = QFrame()
            card.setStyleSheet("""
                QFrame {{
                    background: #0a0a12; border: 1px solid {};
                    border-radius: 10px; padding: 16px;
                }}
            """.format(border_color))
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(10)

            header_row = QHBoxLayout()
            title_label = QLabel(item["title"])
            title_label.setStyleSheet("color: #e0e0e0; font-size: 16px; font-weight: bold;")
            title_label.setWordWrap(True)
            header_row.addWidget(title_label)
            header_row.addStretch()

            badge = QLabel(item["badge"])
            badge.setStyleSheet("""
                color: {}; background: #0d0d18; border: 1px solid {};
                border-radius: 4px; padding: 2px 8px; font-size: 11px; font-weight: 500;
            """.format(badge_color, border_color))
            header_row.addWidget(badge)
            card_layout.addLayout(header_row)

            if item.get("description"):
                desc = QLabel(item["description"])
                desc.setStyleSheet("color: #707080; font-size: 12px;")
                desc.setWordWrap(True)
                card_layout.addWidget(desc)

            self._layout.addWidget(card)

        self._layout.addStretch()

    @staticmethod
    def _border_from(color):
        m = {
            "#6aaae0": "#1a2a3a",
            "#e0c06a": "#3a3a1a",
            "#4ae04a": "#1a3a1a",
            "#e06a6a": "#3a1a1a",
        }
        return m.get(color, "#1a1a2a")

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
