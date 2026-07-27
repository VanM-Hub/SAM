"""
Home Page — Mission-Centric.

Empat pertanyaan:
1. Apa kondisi sistem?  → system_condition
2. Apa yang sedang terjadi? → current_activity
3. Apa yang sedang dilakukan SAM? → sam_action (hanya jika SAM bertindak)
4. Apakah saya perlu melakukan sesuatu? → user_action_needed

Fokus: Mission Target.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton,
)
from PySide6.QtCore import Qt, QTimer

from ...experience.engine import ExperienceEngine
from ..widgets import AttentionBanner
from ..context import ExperienceContextBuilder


class HomePage(QWidget):
    """Home — Mission-Centric. Fokus pada Mission Target."""

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
        # MISSION STATUS CARD — Satu fokus: Mission Target
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

        # Pertanyaan 1: Kondisi sistem
        self._condition = QLabel()
        self._condition.setStyleSheet("color: #e0e0e0; font-size: 22px; font-weight: bold;")
        self._condition.setWordWrap(True)
        f_layout.addWidget(self._condition)

        # Pertanyaan 2: Aktivitas terkini
        self._activity = QLabel()
        self._activity.setStyleSheet("color: #808090; font-size: 14px;")
        self._activity.setWordWrap(True)
        f_layout.addWidget(self._activity)

        # Progress
        self._progress_widget = QFrame()
        p_layout = QVBoxLayout(self._progress_widget)
        p_layout.setContentsMargins(0, 8, 0, 0)
        self._progress_bar = QFrame()
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setStyleSheet("background: #1a1a2a; border-radius: 3px;")
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

        # Pertanyaan 3: SAM action (hanya jika ada)
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

        # Pertanyaan 4: User action needed
        self._user_action = QLabel()
        self._user_action.setStyleSheet("color: #a0a0b0; font-size: 15px; margin-top: 4px;")
        self._user_action.setWordWrap(True)
        f_layout.addWidget(self._user_action)

        # Level 2 button
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
        # RECOMMENDATIONS
        # ===================================================================
        self._rec_title = QLabel("RECOMMENDATIONS")
        self._rec_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px; margin-top: 8px;")
        self._layout.addWidget(self._rec_title)
        self._rec_title.hide()

        self._rec_layout = QVBoxLayout()
        self._rec_layout.setSpacing(6)
        self._layout.addLayout(self._rec_layout)

        # ===================================================================
        # PREDICTIONS
        # ===================================================================
        self._pred_title = QLabel("PREDICTIONS")
        self._pred_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px; margin-top: 8px;")
        self._layout.addWidget(self._pred_title)
        self._pred_title.hide()

        self._pred_layout = QVBoxLayout()
        self._pred_layout.setSpacing(6)
        self._layout.addLayout(self._pred_layout)

        # ===================================================================
        # RECENT ACTIVITY
        # ===================================================================
        self._stories_title = QLabel("RECENT ACTIVITY")
        self._stories_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px; margin-top: 12px;")
        self._layout.addWidget(self._stories_title)

        self._stories_layout = QVBoxLayout()
        self._stories_layout.setSpacing(4)
        self._layout.addLayout(self._stories_layout)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

        self._detail_visible = False
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
        try:
            # Presentation — Mission-Centric
            pres = self.experience.build_presentation()

            # Icon
            icon_map = {
                "Operating normally.": "\u2705",
                "Deployment in progress": "\U0001f3d7\ufe0f",
                "Automatic recovery": "\U0001f504",
                "Action required": "\U0001f6a8",
                "Needs your attention": "\u26a0\ufe0f",
                "New patterns": "\U0001f9e0",
            }
            icon = "\u2705"
            for key, val in icon_map.items():
                if key in pres.system_condition:
                    icon = val
                    break

            self._icon.setText(icon)
            self._condition.setText(pres.system_condition)
            self._activity.setText(pres.current_activity)
            self._user_action.setText(pres.user_action_needed)

            # SAM action (hanya jika bertindak)
            if pres.sam_action:
                self._sam_action.setText("SAM: {}".format(pres.sam_action))
                self._sam_action.show()
            else:
                self._sam_action.hide()

            # Color conditions
            if "Action required" in pres.system_condition:
                color = "#e06a6a"
            elif "Attention" in pres.system_condition or "approval" in pres.system_condition.lower():
                color = "#e0c06a"
            elif "recovery" in pres.system_condition.lower():
                color = "#e0a06a"
            elif "progress" in pres.system_condition.lower():
                color = "#6aaae0"
            else:
                color = "#4ae04a"
            self._condition.setStyleSheet(
                "color: {}; font-size: 22px; font-weight: bold;".format(color)
            )

            # Detail level 2
            self._detail_level2.setText(pres.detail)

            # Context
            ctx = self._ctx_builder.build()
            self._attention.update_from_context(ctx)

            # Recommendations
            self._clear_layout(self._rec_layout)
            recs = self.experience.get_recommendations(limit=3)
            valid_recs = [r for r in recs if r.priority > 10]
            if valid_recs:
                self._rec_title.show()
                for r in valid_recs:
                    self._rec_layout.addWidget(self._rec_card(r))
            else:
                self._rec_title.hide()

            # Predictions
            self._clear_layout(self._pred_layout)
            preds = self.experience.get_predictions(limit=2)
            valid_preds = [p for p in preds if p.risk != "None"]
            if valid_preds:
                self._pred_title.show()
                for p in valid_preds:
                    self._pred_layout.addWidget(self._pred_card(p))
            else:
                self._pred_title.hide()

            # Recent stories
            self._clear_layout(self._stories_layout)
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

    def _rec_card(self, rec):
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: #0a0a12; border: 1px solid #1a1a2a;
                     border-radius: 8px; padding: 8px 12px; }
            QFrame:hover { border: 1px solid #2a2a3a; }
        """)
        layout = QHBoxLayout(card)
        layout.setSpacing(8)
        icon = QLabel("\U0001f4a1")
        icon.setStyleSheet("font-size: 12px;")
        layout.addWidget(icon)
        text = QLabel(rec.reason[:60])
        text.setStyleSheet("color: #c0c0d0; font-size: 12px;")
        text.setWordWrap(True)
        layout.addWidget(text, 1)
        return card

    def _pred_card(self, pred):
        card = QFrame()
        card.setStyleSheet("""
            QFrame { background: #0a0a12; border: 1px solid #1a1a2a;
                     border-left: 3px solid #e0c06a;
                     border-radius: 8px; padding: 8px 12px; }
        """)
        layout = QVBoxLayout(card)
        layout.setSpacing(2)
        text = QLabel(pred.display())
        text.setStyleSheet("color: #c0c0d0; font-size: 12px;")
        text.setWordWrap(True)
        layout.addWidget(text)
        if pred.recommendation_hint:
            hint = QLabel(pred.recommendation_hint)
            hint.setStyleSheet("color: #707080; font-size: 11px;")
            layout.addWidget(hint)
        return card

    @staticmethod
    def _clear_layout(layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
