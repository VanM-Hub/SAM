"""
Notification + Assistant Pages v3.1.

Notification = inbox, bukan popup.
Assistant = jawaban dari Explanation Engine, bukan LLM.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QLineEdit, QTextEdit,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ...experience.engine import ExperienceEngine


# ============================================================================
# NOTIFICATION — Inbox
# ============================================================================

class NotificationPage(QWidget):
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
        title = QLabel("Notifications")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)
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
            model = self.experience.build_notifications()
            self._render(model)
        except Exception:
            pass

    def _render(self, model):
        self._clear()

        for notif in model.items[:20]:
            # Icon per type
            icon_map = {
                "approval": "\u26a0\ufe0f",
                "recommendation": "\U0001f4a1",
                "policy": "\U0001f6e1\ufe0f",
                "update": "\U0001f504",
                "recovery": "\u2705",
            }
            icon = icon_map.get(notif.type, "\U0001f514")
            color = "#e0c06a" if notif.type == "approval" else "#a0a0b0"

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #0a0a12;
                    border: 1px solid #1a1a2a;
                    border-radius: 8px;
                    padding: 10px 14px;
                }
                QFrame:hover {
                    border: 1px solid #2a2a3a;
                }
            """)
            c_layout = QHBoxLayout(card)
            c_layout.setSpacing(12)

            icon_w = QLabel(icon)
            icon_w.setStyleSheet("font-size: 16px;")
            c_layout.addWidget(icon_w)

            # Text
            text_w = QWidget()
            text_layout = QVBoxLayout(text_w)
            text_layout.setContentsMargins(0, 0, 0, 0)
            text_layout.setSpacing(2)

            msg = QLabel(notif.message)
            msg.setStyleSheet("color: {}; font-size: 13px;".format(color))
            msg.setWordWrap(True)
            text_layout.addWidget(msg)

            if notif.timestamp:
                ts = QLabel(notif.timestamp)
                ts.setStyleSheet("color: #505060; font-size: 10px;")
                text_layout.addWidget(ts)

            c_layout.addWidget(text_w, 1)

            # Action button
            if notif.action:
                btn = QPushButton(notif.action)
                btn.setStyleSheet("""
                    QPushButton {
                        background: #1a1a2a;
                        border: 1px solid #2a2a3a;
                        border-radius: 4px;
                        padding: 4px 10px;
                        color: #c0c0d0;
                        font-size: 11px;
                    }
                    QPushButton:hover {
                        background: #2a2a3a;
                    }
                """)
                c_layout.addWidget(btn)

            self._layout.addWidget(card)

        if not model.items or (len(model.items) == 1 and model.items[0].type == "info"):
            empty = QLabel("\U0001f514  No notifications")
            empty.setStyleSheet("color: #606070; font-size: 14px; padding: 24px;")
            self._layout.addWidget(empty)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ============================================================================
# ASSISTANT — Tanya jawab, bukan chatbot
# ============================================================================

class AssistantPage(QWidget):
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
        title = QLabel("Assistant")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)
        sub = QLabel("Ask me anything about SAM.")
        sub.setStyleSheet("color: #606070; font-size: 12px; margin-top: 2px;")
        h_layout.addWidget(sub)
        root.addWidget(header)

        # Scroll area for answers
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
            QPushButton:hover {
                background: #3a5a7a;
            }
        """)
        self.ask_btn.clicked.connect(self._ask)
        input_layout.addWidget(self.ask_btn)

        root.addWidget(input_bar)

        # Suggested questions
        self._add_suggested()

    def _add_suggested(self):
        """Show suggested questions."""
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
            "What is happening?",
            "Is the system healthy?",
            "What do you recommend?",
            "Are there any approvals?",
            "Why is autonomy disabled?",
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
                QPushButton:hover {
                    background: #121222;
                    border: 1px solid #2a2a4a;
                }
            """)
            btn.clicked.connect(lambda checked, q=q: self._ask_suggested(q))
            c_layout.addWidget(btn)

        self._layout.addWidget(container)

    def _ask_suggested(self, question):
        self.question_input.setText(question)
        self._ask()

    def _ask(self):
        question = self.question_input.text().strip()
        if not question:
            return

        answer = self.experience.ask(question)

        # Answer card
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

        # Question
        q_label = QLabel("You: {}".format(question))
        q_label.setStyleSheet("color: #808090; font-size: 12px; font-style: italic;")
        c_layout.addWidget(q_label)

        # Answer
        a_label = QLabel(answer.answer)
        a_label.setStyleSheet("color: #e0e0e0; font-size: 14px;")
        a_label.setWordWrap(True)
        c_layout.addWidget(a_label)

        # Details
        if answer.details:
            d_label = QLabel(answer.details)
            d_label.setStyleSheet("color: #808090; font-size: 11px; padding-left: 8px;")
            d_label.setWordWrap(True)
            c_layout.addWidget(d_label)

        # Action
        if answer.action:
            btn = QPushButton(answer.action)
            btn.setStyleSheet("""
                QPushButton {
                    background: #2a5a3a;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 14px;
                    color: #fff;
                    font-size: 12px;
                    max-width: 100px;
                }
                QPushButton:hover {
                    background: #3a7a4a;
                }
            """)
            c_layout.addWidget(btn)

        self._layout.insertWidget(self._layout.count() - 1, card)
        self.question_input.clear()
