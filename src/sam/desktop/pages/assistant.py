"""
Notification + Assistant Pages v3.1 — Narrative Edition.

Notification = Narrative cards.
Assistant = Narrative-aware answers.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QLineEdit,
)
from PySide6.QtCore import Qt, QTimer

from ...experience.engine import ExperienceEngine


# ============================================================================
# NOTIFICATION — Narrative cards
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
            model = self.experience.build_notifications()
            narratives = self.experience.narrative.build_from_notifications(model)
            attention_items = self.experience.get_all_attention()
            self._render(model, narratives, attention_items)
        except Exception:
            pass

    def _render(self, model, narratives, attention_items=None):
        self._clear()
        has_items = False

        # Attention items
        if attention_items:
            for item in attention_items[:10]:
                has_items = True
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {{
                        background: #0a0a12;
                        border: 1px solid {};
                        border-radius: 8px;
                        padding: 10px 14px;
                    }}
                    QFrame:hover {{ border: 1px solid #3a3a5a; }}
                """.format(item.color))
                c_layout = QVBoxLayout(card)
                c_layout.setSpacing(2)
                row = QHBoxLayout()
                from ...operations.attention import SCORE_TO_LABEL
                label = SCORE_TO_LABEL.get(item.score, "Normal")
                score = QLabel("[{}]".format(label))
                score.setStyleSheet("color: {}; font-size: 10px; font-weight: bold;".format(item.color))
                row.addWidget(score)
                text = QLabel(item.message or item.title)
                text.setStyleSheet("color: #c0c0d0; font-size: 13px;")
                text.setWordWrap(True)
                row.addWidget(text, 1)
                c_layout.addLayout(row)
                if item.reason:
                    r = QLabel(item.reason)
                    r.setStyleSheet("color: #707080; font-size: 11px; padding-left: 16px;")
                    r.setWordWrap(True)
                    c_layout.addWidget(r)
                self._layout.addWidget(card)

        # Narrative cards first
        for n in narratives:
            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #0a0a12;
                    border: 1px solid #2a2a4a;
                    border-radius: 8px;
                    padding: 10px 14px;
                }
                QFrame:hover {
                    border: 1px solid #3a3a5a;
                }
            """)
            c_layout = QVBoxLayout(card)
            c_layout.setSpacing(2)

            icon_map = {
                "action_required": "\u26a0\ufe0f",
                "attention": "\U0001f4a1",
                "information": "\U0001f514",
                "critical": "\U0001f6a8",
            }
            icon = icon_map.get(n.importance.value, "\U0001f514")

            row = QHBoxLayout()
            i_w = QLabel(icon)
            i_w.setStyleSheet("font-size: 14px;")
            row.addWidget(i_w)

            text = QLabel(n.title)
            text.setStyleSheet("color: #c0c0d0; font-size: 13px;")
            text.setWordWrap(True)
            row.addWidget(text, 1)
            c_layout.addLayout(row)

            if n.details:
                d = QLabel(n.details)
                d.setStyleSheet("color: #707080; font-size: 11px; padding-left: 20px;")
                d.setWordWrap(True)
                c_layout.addWidget(d)

            if n.recommended_action:
                btn = QPushButton(n.recommended_action)
                btn.setStyleSheet("""
                    QPushButton {
                        background: #1a1a2a;
                        border: 1px solid #2a2a3a;
                        border-radius: 4px;
                        padding: 4px 10px;
                        color: #c0c0d0;
                        font-size: 11px;
                        max-width: 100px;
                    }
                    QPushButton:hover {
                        background: #2a2a3a;
                    }
                """)
                c_layout.addWidget(btn)

            self._layout.addWidget(card)

        if not narratives:
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
# ASSISTANT — Narrative-aware
# ============================================================================

class AssistantPage(QWidget):
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
            "Good morning briefing",
            "What happened today?",
            "What is the current situation?",
            "Anything needs attention?",
            "Show unfinished work.",
            "What has the system learned?",
            "Why is action needed?",
            "Are there any approvals?",
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

        answer = self.experience.ask(question)

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

        a_label = QLabel(answer.answer)
        a_label.setStyleSheet("color: #e0e0e0; font-size: 14px;")
        a_label.setWordWrap(True)
        c_layout.addWidget(a_label)

        if answer.details:
            d_label = QLabel(answer.details)
            d_label.setStyleSheet("color: #808090; font-size: 11px; padding-left: 8px;")
            d_label.setWordWrap(True)
            c_layout.addWidget(d_label)

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
                QPushButton:hover { background: #3a7a4a; }
            """)
            c_layout.addWidget(btn)

        self._layout.insertWidget(self._layout.count() - 1, card)
        self.question_input.clear()
