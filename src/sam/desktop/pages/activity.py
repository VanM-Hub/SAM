"""
Activity Page v4.0 — Conversation-powered.

'What happened?'
Menggunakan Conversation.answer() untuk timeline.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QLineEdit,
)
from PySide6.QtCore import Qt, QTimer

from ...operations.conversation_api import Conversation
from ..widgets import TimelineWidget, StatusCard


class ActivityPage(QWidget):
    """Activity — 'What happened?' — dari Conversation."""

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
        h_layout.setSpacing(8)

        title = QLabel("Activity")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)
        sub = QLabel("What happened — told in moments, not in logs.")
        sub.setStyleSheet("color: #606070; font-size: 12px;")
        h_layout.addWidget(sub)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter activity...")
        self.search_input.setStyleSheet("""
            QLineEdit { background: #0a0a12; border: 1px solid #1a1a2a;
                        border-radius: 8px; padding: 8px 14px;
                        color: #e0e0e0; font-size: 12px; max-width: 300px; }
            QLineEdit:focus { border: 1px solid #2a2a4a; }
        """)
        self.search_input.textChanged.connect(self.refresh)
        h_layout.addWidget(self.search_input)

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
        self._layout.setSpacing(0)

        # Timeline reusable widget
        self._timeline = TimelineWidget()
        self._layout.addWidget(self._timeline)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(10000)
        self.refresh()

    def update_context(self, ctx):
        pass

    def refresh(self):
        try:
            # ================================================================
            # DARI Conversation — answer(CHANGES)
            # ================================================================
            answer = self.conversation.answer("What changed?")
            query = self.search_input.text().lower()

            # Bangun kelompok dari answer.sections
            groups = []
            if answer.sections:
                for label, text in answer.sections[:7]:
                    # Parse text jadi entries
                    lines = [l.strip() for l in text.split("\n") if l.strip()]
                    if query:
                        lines = [l for l in lines if query in l.lower()]
                    if lines:
                        entries = [(l, "") for l in lines[:15]]
                        groups.append((label, entries))

            self._timeline.set_groups(groups)

        except Exception:
            pass
