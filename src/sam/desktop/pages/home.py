"""
Home Page — Jawaban dari Conversation.

Home bukan lagi page yang membangun widget sendiri.
Home cuma: conversation.answer("What's happening?") → render.

Tidak ada narasi buatan sendiri.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton,
)
from PySide6.QtCore import Qt, QTimer

from ...operations.conversation_api import Conversation
from ..widgets import AttentionBanner
from ..context import DesktopContextBuilder


class HomePage(QWidget):
    """Home — Mission-Centric. Cuma render jawaban Conversation."""

    def __init__(self, conversation: Conversation):
        super().__init__()
        self.conversation = conversation
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

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
        self._layout.setContentsMargins(24, 24, 24, 32)
        self._layout.setSpacing(12)

        # ===================================================================
        # FOCUS CARD — Mission Condition
        # ===================================================================
        self._focus_card = QFrame()
        self._focus_card.setStyleSheet("""
            QFrame {
                background: #08080f;
                border: 1px solid #141422;
                border-radius: 16px;
                padding: 28px 24px;
            }
        """)
        f_layout = QVBoxLayout(self._focus_card)
        f_layout.setSpacing(4)

        self._target_label = QLabel("WORKSPACE")
        self._target_label.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px;")
        f_layout.addWidget(self._target_label)

        self._icon = QLabel()
        self._icon.setStyleSheet("font-size: 28px;")
        f_layout.addWidget(self._icon)

        self._condition = QLabel()
        self._condition.setStyleSheet("color: #e0e0e0; font-size: 22px; font-weight: bold;")
        self._condition.setWordWrap(True)
        f_layout.addWidget(self._condition)

        self._activity = QLabel()
        self._activity.setStyleSheet("color: #808090; font-size: 14px;")
        self._activity.setWordWrap(True)
        f_layout.addWidget(self._activity)

        self._sam_action = QLabel()
        self._sam_action.setStyleSheet("""
            color: #6aaae0;
            font-size: 14px;
            padding: 8px 12px;
            background: #0a0a18;
            border-radius: 6px;
            margin-top: 8px;
        """)
        self._sam_action.setWordWrap(True)
        self._sam_action.hide()
        f_layout.addWidget(self._sam_action)

        self._user_action = QLabel()
        self._user_action.setStyleSheet("color: #a0a0b0; font-size: 15px; margin-top: 4px;")
        self._user_action.setWordWrap(True)
        f_layout.addWidget(self._user_action)

        self._detail_btn = QPushButton("Show technical details")
        self._detail_btn.setCursor(Qt.PointingHandCursor)
        self._detail_btn.setStyleSheet("""
            QPushButton { background: transparent; border: 1px solid #1a1a2a;
                          border-radius: 6px; padding: 6px 14px;
                          color: #606070; font-size: 11px; margin-top: 8px; }
            QPushButton:hover { background: #121222; color: #a0a0b0; }
        """)
        self._detail_btn.clicked.connect(self._toggle_details)
        f_layout.addWidget(self._detail_btn)

        self._detail_level2 = QLabel()
        self._detail_level2.setStyleSheet("""
            color: #505060; font-size: 11px; padding: 12px;
            background: #0a0a12; border-radius: 6px; margin-top: 4px;
        """)
        self._detail_level2.setWordWrap(True)
        self._detail_level2.hide()
        f_layout.addWidget(self._detail_level2)

        self._layout.addWidget(self._focus_card)

        # ===================================================================
        # Attention Banner
        # ===================================================================
        self._attention = AttentionBanner()
        self._attention.action_clicked.connect(lambda a: self._switch_alerts())
        self._layout.addWidget(self._attention)
        self._attention.hide()

        # ===================================================================
        # RECOMMENDATIONS — dari Conversation
        # ===================================================================
        self._rec_title = QLabel("RECOMMENDATIONS")
        self._rec_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px; margin-top: 8px;")
        self._layout.addWidget(self._rec_title)
        self._rec_title.hide()

        self._rec_layout = QVBoxLayout()
        self._rec_layout.setSpacing(6)
        self._layout.addLayout(self._rec_layout)

        # ===================================================================
        # PREDICTIONS — dari Conversation
        # ===================================================================
        self._pred_title = QLabel("PREDICTIONS")
        self._pred_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px; margin-top: 8px;")
        self._layout.addWidget(self._pred_title)
        self._pred_title.hide()

        self._pred_layout = QVBoxLayout()
        self._pred_layout.setSpacing(6)
        self._layout.addLayout(self._pred_layout)

        # ===================================================================
        # RECENT CHANGES — dari Conversation
        # ===================================================================
        self._stories_title = QLabel("RECENT CHANGES")
        self._stories_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px; margin-top: 12px;")
        self._layout.addWidget(self._stories_title)

        self._stories_layout = QVBoxLayout()
        self._stories_layout.setSpacing(4)
        self._layout.addLayout(self._stories_layout)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

        self._detail_visible = False
        self._last_answer = None

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)
        self.refresh()

    def _switch_alerts(self):
        parent = self.parent()
        if parent and hasattr(parent, 'switch_page'):
            parent.switch_page(6)

    def _toggle_details(self):
        self._detail_visible = not self._detail_visible
        self._detail_level2.setVisible(self._detail_visible)
        self._detail_btn.setText(
            "Hide technical details" if self._detail_visible
            else "Show technical details"
        )

    def refresh(self):
        """Refresh Home — cukup tanya Conversation."""
        try:
            # ================================================================
            # SATU PANGGILAN — semua dari Conversation
            # ================================================================
            answer = self.conversation.answer("What's happening?")
            self._last_answer = answer

            # Icon
            icon_map = {
                "normal": "\u2705",
                "progress": "\U0001f3d7\ufe0f",
                "recovery": "\U0001f504",
                "action": "\U0001f6a8",
                "attention": "\u26a0\ufe0f",
                "learning": "\U0001f9e0",
            }
            title_lower = (answer.title or "").lower()
            icon = "\u2705"
            for key, val in icon_map.items():
                if key in title_lower:
                    icon = val
                    break

            self._icon.setText(icon)

            # Condition color
            color = "#4ae04a"
            if "action" in title_lower or "required" in title_lower:
                color = "#e06a6a"
            elif "attention" in title_lower or "approval" in title_lower:
                color = "#e0c06a"
            elif "recovery" in title_lower:
                color = "#e0a06a"
            elif "progress" in title_lower:
                color = "#6aaae0"

            self._condition.setText(answer.title or "")
            self._condition.setStyleSheet(
                "color: {}; font-size: 22px; font-weight: bold;".format(color)
            )
            self._activity.setText(answer.summary or "")
            self._user_action.setText(answer.user_action_needed or "")

            # SAM action
            if answer.sam_action:
                self._sam_action.setText("SAM: {}".format(answer.sam_action))
                self._sam_action.show()
            else:
                self._sam_action.hide()

            # Detail level 2
            self._detail_level2.setText(answer.technical_details or answer.details or "")

            # Recommendations — dari HumanAnswer
            self._clear_layout(self._rec_layout)
            if answer.recommendations:
                self._rec_title.show()
                for r in answer.recommendations:
                    self._rec_layout.addWidget(self._text_card(r, "\U0001f4a1"))
            else:
                self._rec_title.hide()

            # Predictions
            self._clear_layout(self._pred_layout)
            if answer.predictions:
                self._pred_title.show()
                for p in answer.predictions:
                    self._pred_layout.addWidget(self._text_card(p, "\U0001f52e"))
            else:
                self._pred_title.hide()

            # Recent changes — dari HumanAnswer.stories
            self._clear_layout(self._stories_layout)
            if answer.stories:
                self._stories_title.show()
                for s in answer.stories[:5]:
                    card = self._text_card(s, "\u2705", small=True)
                    self._stories_layout.addWidget(card)
            else:
                self._stories_title.hide()

        except Exception as e:
            self._condition.setText("Unable to load.")
            self._activity.setText(str(e))

    def _text_card(self, text, icon_char="\u2705", small=False):
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: #0a0a12; border: 1px solid #1a1a2a;
                     border-radius: 8px; padding: 8px 12px; }
            QFrame:hover { border: 1px solid #2a2a3a; }
        """)
        layout = QHBoxLayout(card)
        layout.setSpacing(8)
        icon = QLabel(icon_char)
        icon.setStyleSheet("font-size: 12px;")
        layout.addWidget(icon)
        txt = QLabel(text[:80])
        txt.setStyleSheet("color: #c0c0d0; font-size: 12px;")
        txt.setWordWrap(True)
        layout.addWidget(txt, 1)
        return card

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
