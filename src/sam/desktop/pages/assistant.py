"""
Notification + Assistant Pages v4.0 — Conversation-powered.

Notification = Conversation.answer() → alerts.
Assistant = Conversation.answer() → tanya langsung.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QLineEdit,
)
from PySide6.QtCore import Qt, QTimer

from ...operations.conversation_api import Conversation


# ============================================================================
# NOTIFICATION — dari Conversation
# ============================================================================

class NotificationPage(QWidget):
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
        title = QLabel("Alerts")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)
        sub = QLabel("What requires your attention.")
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
        self._layout.setSpacing(6)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(10000)
        self.refresh()

    def refresh(self):
        try:
            # ================================================================
            # DARI Conversation — answer() untuk alert
            # ================================================================
            overview = self.conversation.answer("What's happening?")
            actions = self.conversation.actions()
            self._render(overview, actions)
        except Exception:
            pass

    def _render(self, overview, actions):
        self._clear()
        has_items = False

        # User action needed sebagai kartu utama
        if overview.user_action_needed and "No action" not in overview.user_action_needed:
            has_items = True
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #0a0a12;
                    border: 1px solid #3a3a1a;
                    border-radius: 8px;
                    padding: 10px 14px;
                }
                QFrame:hover { border: 1px solid #3a3a5a; }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(2)
            row = QHBoxLayout()
            score = QLabel("[ACTION REQUIRED]")
            score.setStyleSheet("color: #e0c06a; font-size: 10px; font-weight: bold;")
            row.addWidget(score)
            text = QLabel(overview.user_action_needed)
            text.setStyleSheet("color: #c0c0d0; font-size: 13px;")
            text.setWordWrap(True)
            row.addWidget(text, 1)
            c_layout.addLayout(row)
            if overview.summary:
                r = QLabel(overview.summary)
                r.setStyleSheet("color: #707080; font-size: 11px; padding-left: 16px;")
                r.setWordWrap(True)
                c_layout.addWidget(r)
            self._layout.addWidget(card)

        # Actions
        if actions.actions:
            for action in actions.actions:
                has_items = True
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background: #0a0a12;
                        border: 1px solid #3a3a1a;
                        border-radius: 8px;
                        padding: 10px 14px;
                    }
                    QFrame:hover { border: 1px solid #3a3a5a; }
                """)
                c_layout = QVBoxLayout(card)
                c_layout.setSpacing(2)
                row = QHBoxLayout()
                score = QLabel("[ACTION]")
                score.setStyleSheet("color: #e0c06a; font-size: 10px; font-weight: bold;")
                row.addWidget(score)
                text = QLabel(action)
                text.setStyleSheet("color: #c0c0d0; font-size: 13px;")
                text.setWordWrap(True)
                row.addWidget(text, 1)
                c_layout.addLayout(row)
                self._layout.addWidget(card)

        # Predictions sebagai "forecast alerts"
        if overview.predictions:
            for p in overview.predictions[:3]:
                has_items = True
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background: #0a0a12;
                        border: 1px solid #2a2a4a;
                        border-radius: 8px;
                        padding: 10px 14px;
                    }
                    QFrame:hover { border: 1px solid #3a3a5a; }
                """)
                c_layout = QVBoxLayout(card)
                c_layout.setSpacing(2)
                row = QHBoxLayout()
                score = QLabel("[PREDICTION]")
                score.setStyleSheet("color: #aa80c0; font-size: 10px; font-weight: bold;")
                row.addWidget(score)
                text = QLabel(p)
                text.setStyleSheet("color: #c0c0d0; font-size: 13px;")
                text.setWordWrap(True)
                row.addWidget(text, 1)
                c_layout.addLayout(row)
                self._layout.addWidget(card)

        if not has_items:
            empty = QLabel("\U0001f514  No alerts")
            empty.setStyleSheet("color: #606070; font-size: 14px; padding: 24px;")
            self._layout.addWidget(empty)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ============================================================================
# ASSISTANT — Conversation-powered
# ============================================================================

class AssistantPage(QWidget):
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
        title = QLabel("Ask")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)
        sub = QLabel("Ask me anything about the system.")
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
        self._layout.setSpacing(8)

        scroll.setWidget(self.content)
        root.addWidget(scroll, 1)

        # Input bar
        input_bar = QWidget()
        input_bar.setStyleSheet("""
            background: #0d0d16;
            border-top: 1px solid #1a1a2a;
            padding: 12px 24px;
        """)
        input_layout = QHBoxLayout(input_bar)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        self.question_input = QLineEdit()
        self.question_input.setPlaceholderText("Ask a question...")
        self.question_input.setStyleSheet("""
            QLineEdit {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 8px;
                padding: 10px 14px;
                color: #e0e0e0;
                font-size: 13px;
            }
            QLineEdit:focus {
                border: 1px solid #2a2a4a;
            }
        """)
        self.question_input.returnPressed.connect(self._ask)
        input_layout.addWidget(self.question_input, 1)

        self.ask_btn = QPushButton("Ask")
        self.ask_btn.setStyleSheet("""
            QPushButton {
                background: #2a4a6a;
                border: none;
                border-radius: 8px;
                padding: 8px 20px;
                color: #fff;
                font-size: 13px;
                font-weight: 500;
            }
            QPushButton:hover { background: #3a5a7a; }
        """)
        self.ask_btn.clicked.connect(self._ask)
        input_layout.addWidget(self.ask_btn)

        root.addWidget(input_bar)

        self._add_suggested()

    def _add_suggested(self):
        container = QFrame()
        container.setStyleSheet("""
            QFrame {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 8px;
                padding: 16px;
            }
        """)
        c_layout = QVBoxLayout(container)
        c_layout.setSpacing(8)

        tip = QLabel("Try asking:")
        tip.setStyleSheet("color: #606070; font-size: 11px; letter-spacing: 1px;")
        c_layout.addWidget(tip)

        questions = [
            "What's happening?",
            "Is everything okay?",
            "Do I need to do anything?",
            "Why?",
            "What changed?",
            "What should happen next?",
            "What happens if nothing is done?",
            "Show technical details.",
        ]
        for q in questions:
            btn = QPushButton(q)
            btn.setCursor(Qt.PointingHandCursor)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    background: transparent;
                    border: 1px solid #1a1a2a;
                    border-radius: 6px;
                    padding: 6px 12px;
                    color: #6aaae0;
                    font-size: 12px;
                }
                QPushButton:hover { background: #121222; border: 1px solid #2a2a4a; }
            """)
            btn.clicked.connect(lambda *a, q=q: self._ask_suggested(q))
            c_layout.addWidget(btn)

        self._layout.addWidget(container)

    def _ask_suggested(self, question):
        self.question_input.setText(question)
        self._ask()

    def _ask(self):
        question = self.question_input.text().strip()
        if not question:
            return

        # ================================================================
        # SATU PANGGILAN — Conversation.answer()
        # ================================================================
        answer = self.conversation.answer(question)

        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: #0a0a12;
                border: 1px solid #2a2a4a;
                border-radius: 8px;
                padding: 14px;
            }
        """)
        c_layout = QVBoxLayout(card)
        c_layout.setSpacing(6)

        q_label = QLabel("You: {}".format(question))
        q_label.setStyleSheet("color: #707080; font-size: 12px; font-style: italic;")
        c_layout.addWidget(q_label)

        # Title
        a_title = QLabel(answer.title or "")
        a_title.setStyleSheet("color: #e0e0e0; font-size: 14px; font-weight: bold;")
        a_title.setWordWrap(True)
        c_layout.addWidget(a_title)

        # Summary
        if answer.summary:
            a_summary = QLabel(answer.summary)
            a_summary.setStyleSheet("color: #b0b0c0; font-size: 13px;")
            a_summary.setWordWrap(True)
            c_layout.addWidget(a_summary)

        # SAM action
        if answer.sam_action:
            sam_lbl = QLabel("SAM: {}".format(answer.sam_action))
            sam_lbl.setStyleSheet("color: #6aaae0; font-size: 12px; padding-left: 4px; margin-top: 4px;")
            c_layout.addWidget(sam_lbl)

        # User action needed
        if answer.user_action_needed and answer.user_action_needed != "No action required.":
            action_lbl = QLabel("\U0001f6a8 {}".format(answer.user_action_needed))
            action_lbl.setStyleSheet("color: #e0c06a; font-size: 12px; padding-left: 4px; margin-top: 2px;")
            c_layout.addWidget(action_lbl)

        # Recommendations
        if answer.recommendations:
            rec_title = QLabel("Recommendations:")
            rec_title.setStyleSheet("color: #808090; font-size: 11px; margin-top: 6px;")
            c_layout.addWidget(rec_title)
            for r in answer.recommendations:
                r_lbl = QLabel("  \U0001f4a1 {}".format(r))
                r_lbl.setStyleSheet("color: #c0c0d0; font-size: 11px;")
                c_layout.addWidget(r_lbl)

        # Predictions
        if answer.predictions:
            pred_title = QLabel("Predictions:")
            pred_title.setStyleSheet("color: #808090; font-size: 11px; margin-top: 4px;")
            c_layout.addWidget(pred_title)
            for p in answer.predictions:
                p_lbl = QLabel("  \U0001f52e {}".format(p))
                p_lbl.setStyleSheet("color: #c0c0d0; font-size: 11px;")
                c_layout.addWidget(p_lbl)

        # Details (Level 2)
        if answer.details:
            d_label = QLabel(answer.details)
            d_label.setStyleSheet("color: #808090; font-size: 11px; padding-left: 8px; margin-top: 4px;")
            d_label.setWordWrap(True)
            c_layout.addWidget(d_label)

        self._layout.insertWidget(self._layout.count() - 1, card)
        self.question_input.clear()
