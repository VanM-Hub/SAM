"""
Home Page v3.2 — Human Experience.

SATU fokus. BUKAN dashboard.
'What is happening?' — jawab dalam < 10 detik.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton,
)
from PySide6.QtCore import Qt, QTimer

from ...experience.engine import ExperienceEngine
from ..widgets import StatusCard, AttentionBanner
from ..context import ExperienceContextBuilder


class HomePage(QWidget):
    """Home — 'What is happening?' — satu fokus."""

    def __init__(self, experience, ctx_builder):
        super().__init__()
        self.experience = experience
        self._ctx_builder = ctx_builder
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
        # HUMAN STATUS CARD — Satu fokus besar
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
        f_layout.setSpacing(8)

        self._focus_icon = QLabel()
        self._focus_icon.setStyleSheet("font-size: 32px;")
        f_layout.addWidget(self._focus_icon)

        self._focus_message = QLabel()
        self._focus_message.setStyleSheet("color: #e0e0e0; font-size: 24px; font-weight: bold;")
        self._focus_message.setWordWrap(True)
        f_layout.addWidget(self._focus_message)

        self._focus_detail = QLabel()
        self._focus_detail.setStyleSheet("color: #808090; font-size: 14px;")
        self._focus_detail.setWordWrap(True)
        f_layout.addWidget(self._focus_detail)

        self._focus_action = QLabel()
        self._focus_action.setStyleSheet("color: #a0a0b0; font-size: 15px; margin-top: 8px;")
        self._focus_action.setWordWrap(True)
        f_layout.addWidget(self._focus_action)

        # Progress bar untuk deployment
        self._progress_widget = QFrame()
        p_layout = QVBoxLayout(self._progress_widget)
        p_layout.setContentsMargins(0, 4, 0, 0)
        self._progress_bar = QFrame()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setStyleSheet("""
            QFrame {
                background: #1a1a2a;
                border-radius: 3px;
            }
        """)
        self._progress_fill = QFrame(self._progress_bar)
        self._progress_fill.setFixedHeight(6)
        self._progress_fill.setStyleSheet("background: #2a6a4a; border-radius: 3px;")
        self._progress_fill.setFixedWidth(0)
        p_layout.addWidget(self._progress_bar)
        self._progress_label = QLabel()
        self._progress_label.setStyleSheet("color: #606070; font-size: 12px;")
        p_layout.addWidget(self._progress_label)
        f_layout.addWidget(self._progress_widget)
        self._progress_widget.hide()

        # Button untuk level 2
        self._detail_btn = QPushButton("Show technical details")
        self._detail_btn.setCursor(Qt.PointingHandCursor)
        self._detail_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #1a1a2a;
                border-radius: 6px;
                padding: 6px 14px;
                color: #606070;
                font-size: 11px;
                margin-top: 8px;
            }
            QPushButton:hover { background: #121222; color: #a0a0b0; }
        """)
        self._detail_btn.clicked.connect(self._toggle_details)
        f_layout.addWidget(self._detail_btn)

        self._detail_level2 = QLabel()
        self._detail_level2.setStyleSheet("""
            color: #505060;
            font-size: 11px;
            padding: 12px;
            background: #0a0a12;
            border-radius: 6px;
            margin-top: 4px;
        """)
        self._detail_level2.setWordWrap(True)
        self._detail_level2.hide()
        f_layout.addWidget(self._detail_level2)

        self._layout.addWidget(self._focus_card)

        # ===================================================================
        # Attention Banner
        # ===================================================================
        self._attention = AttentionBanner()
        self._attention.action_clicked.connect(lambda a: self._switch_activity())
        self._layout.addWidget(self._attention)
        self._attention.hide()

        # ===================================================================
        # ATTENTION TOP 3
        # ===================================================================
        self._top3_title = QLabel("ATTENTION")
        self._top3_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px; margin-top: 8px;")
        self._layout.addWidget(self._top3_title)
        self._top3_title.hide()

        self._top3_layout = QVBoxLayout()
        self._top3_layout.setSpacing(6)
        self._layout.addLayout(self._top3_layout)

        # ===================================================================
        # RECENT STORIES
        # ===================================================================
        self._stories_title = QLabel("RECENT ACTIVITY")
        self._stories_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px; margin-top: 12px;")
        self._layout.addWidget(self._stories_title)

        self._stories_layout = QVBoxLayout()
        self._stories_layout.setSpacing(6)
        self._layout.addLayout(self._stories_layout)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

        self._detail_visible = False
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)
        self.refresh()

    def _switch_activity(self):
        parent = self.parent()
        if parent and hasattr(parent, 'switch_page'):
            parent.switch_page(6)

    def _toggle_details(self):
        self._detail_visible = not self._detail_visible
        if self._detail_visible:
            self._detail_level2.show()
            self._detail_btn.setText("Hide technical details")
        else:
            self._detail_level2.hide()
            self._detail_btn.setText("Show technical details")

    def update_context(self, ctx):
        pass

    def refresh(self):
        try:
            # Situasi — satu fokus
            sit = self.experience.detect_situation()
            self._focus_icon.setText(sit.icon)
            self._focus_message.setText(sit.focus_message)
            self._focus_message.setStyleSheet(
                "color: {}; font-size: 24px; font-weight: bold;".format(sit.color)
            )
            self._focus_detail.setText(sit.focus_detail)
            self._focus_action.setText(sit.action_message)

            self._detail_level2.setText(sit.detail_level2)

            # Progress
            if sit.situation.value == "deployment_running" and sit.progress_percent > 0:
                self._progress_fill.setFixedWidth(
                    int(self._progress_bar.width() * sit.progress_percent / 100)
                )
                self._progress_label.setText(
                    "{}%  —  Estimated completion: {}".format(
                        sit.progress_percent, sit.estimated_time or "unknown"
                    )
                )
                self._progress_widget.show()
            else:
                self._progress_widget.hide()

            # Context
            ctx = self._ctx_builder.build()
            self._attention.update_from_context(ctx)

            # Attention Top 3
            self._clear_top3()
            top3 = self.experience.get_attention_top(3)
            if top3:
                self._top3_title.show()
                for item in top3:
                    card = QFrame()
                    card.setStyleSheet("""
                        QFrame { background: #0a0a12; border: 1px solid #1a1a2a;
                                 border-radius: 8px; padding: 8px 12px; }
                        QFrame:hover { border: 1px solid #2a2a3a; }
                    """)
                    c_layout = QHBoxLayout(card)
                    c_layout.setSpacing(8)

                    score_color = item.color
                    score = QLabel("[{}]".format(item.score))
                    score.setStyleSheet("color: {}; font-size: 11px; font-weight: bold;".format(score_color))
                    c_layout.addWidget(score)

                    text = QLabel(item.title[:60])
                    text.setStyleSheet("color: #c0c0d0; font-size: 12px;")
                    text.setWordWrap(True)
                    c_layout.addWidget(text, 1)

                    self._top3_layout.addWidget(card)
            else:
                self._top3_title.hide()

            # Recent stories
            self._clear_stories()
            stories = self.experience.build_activity_stories()
            if stories:
                self._stories_title.show()
                for story in stories[:5]:
                    card = QFrame()
                    card.setStyleSheet("""
                        QFrame { background: transparent; border: none; padding: 2px 0; }
                        QFrame:hover { background: #0d0d18; border-radius: 4px; }
                    """)
                    c_layout = QHBoxLayout(card)
                    c_layout.setContentsMargins(4, 2, 4, 2)
                    c_layout.setSpacing(8)

                    icon = QLabel(story.icon)
                    icon.setStyleSheet("font-size: 13px;")
                    c_layout.addWidget(icon)

                    text = QLabel(story.title)
                    text.setStyleSheet("color: #b0b0c0; font-size: 13px;")
                    text.setWordWrap(True)
                    c_layout.addWidget(text, 1)

                    if story.duration:
                        dur = QLabel(story.duration)
                        dur.setStyleSheet("color: #606070; font-size: 10px;")
                        c_layout.addWidget(dur)

                    self._stories_layout.addWidget(card)
            else:
                self._stories_title.hide()

        except Exception:
            pass

    def _clear_top3(self):
        while self._top3_layout.count():
            item = self._top3_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _clear_stories(self):
        while self._stories_layout.count():
            item = self._stories_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
