"""
Home Page v3.1 — Narrative Edition.

Bukan dashboard.
Bukan monitoring.
Singkat — 5 detik — cerita.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, QTimer

from ...experience.engine import ExperienceEngine


class HomePage(QWidget):
    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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
        self._layout.setContentsMargins(24, 32, 24, 32)
        self._layout.setSpacing(0)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)
        self.refresh()

    def refresh(self):
        try:
            model = self.experience.build_home()
            narrative = self.experience.build_narrative_home()
            briefing = self.experience.build_daily_briefing()
            situation = self.experience.build_situation_brief()
            self._render(model, narrative, briefing, situation)
        except Exception:
            pass

    def _render(self, model, narrative, briefing, situation):
        self._clear()

        # ===================================================================
        # 1. GREETING — Narrative, bukan data
        # ===================================================================
        greeting_card = QFrame()
        greeting_card.setStyleSheet("""
            QFrame {
                background: #08080f;
                border: 1px solid #141422;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        g_layout = QVBoxLayout(greeting_card)
        g_layout.setSpacing(4)

        greeting = QLabel(briefing.greeting)
        greeting.setStyleSheet("color: #e0e0e0; font-size: 24px; font-weight: bold;")
        g_layout.addWidget(greeting)

        # Primary narrative
        pri = narrative.primary
        if pri:
            if model.health.status.value == "healthy":
                color = "#4ae04a"
            else:
                color = "#e0c06a"

            p_text = QLabel(pri.title)
            p_text.setStyleSheet("color: {}; font-size: 16px; margin-top: 8px;".format(color))
            p_text.setWordWrap(True)
            g_layout.addWidget(p_text)

            if pri.details:
                d = QLabel(pri.details)
                d.setStyleSheet("color: #808090; font-size: 12px;")
                d.setWordWrap(True)
                g_layout.addWidget(d)

        self._layout.addWidget(greeting_card)
        self._layout.addSpacing(12)

        # ===================================================================
        # 2. SITUATION BRIEF — Narrative
        # ===================================================================
        sit_card = QFrame()
        sit_card.setStyleSheet("""
            QFrame {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        sit_layout = QVBoxLayout(sit_card)
        sit_layout.setSpacing(4)

        sit_lines = [
            situation.summary,
            situation.health_statement,
            situation.incident_statement,
            situation.work_statement,
        ]
        for line in sit_lines:
            l = QLabel(line)
            l.setStyleSheet("color: #c0c0d0; font-size: 14px;")
            l.setWordWrap(True)
            sit_layout.addWidget(l)

        self._layout.addWidget(sit_card)
        self._layout.addSpacing(16)

        # ===================================================================
        # 3. ACTION REQUIRED
        # ===================================================================
        if narrative.action_count > 0:
            action_card = QFrame()
            action_card.setStyleSheet("""
                QFrame {
                    background: #1a1a0a;
                    border: 1px solid #3a3a1a;
                    border-radius: 10px;
                    padding: 16px;
                }
            """)
            a_layout = QVBoxLayout(action_card)
            a_layout.setSpacing(4)

            required = QLabel("\u26a0\ufe0f  Action required")
            required.setStyleSheet("color: #e0c06a; font-size: 15px; font-weight: bold;")
            a_layout.addWidget(required)

            for n in narrative.supporting:
                if n.action_required:
                    item = QLabel("  {} – {}".format(
                        n.title[:40],
                        n.recommended_action[:40] if n.recommended_action else "Review required"
                    ))
                    item.setStyleSheet("color: #c0c0b0; font-size: 13px;")
                    item.setWordWrap(True)
                    a_layout.addWidget(item)

            self._layout.addWidget(action_card)
            self._layout.addSpacing(12)

        # ===================================================================
        # 4. SUPPORTING NARRATIVES — recommendations, updates
        # ===================================================================
        for n in narrative.supporting:
            if n.importance.value in ("attention", "information"):
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background: #0a0a12;
                        border: 1px solid #1a1a2a;
                        border-radius: 8px;
                        padding: 12px 16px;
                    }
                    QFrame:hover {
                        border: 1px solid #2a2a3a;
                    }
                """)
                c_layout = QVBoxLayout(card)
                c_layout.setSpacing(2)

                if n.importance == "attention":
                    icon = "\U0001f4a1"
                else:
                    icon = "\U0001f4cc"

                row = QHBoxLayout()
                title = QLabel("{}  {}".format(icon, n.title))
                title.setStyleSheet("color: #c0c0d0; font-size: 13px;")
                title.setWordWrap(True)
                row.addWidget(title, 1)
                c_layout.addLayout(row)

                if n.details:
                    d = QLabel(n.details)
                    d.setStyleSheet("color: #707080; font-size: 11px; padding-left: 20px;")
                    d.setWordWrap(True)
                    c_layout.addWidget(d)

                if n.estimated_impact:
                    imp = QLabel("Impact: {}".format(n.estimated_impact))
                    imp.setStyleSheet("color: #606070; font-size: 11px; padding-left: 20px;")
                    c_layout.addWidget(imp)

                self._layout.addWidget(card)
                self._layout.addSpacing(6)

        # ===================================================================
        # 5. BRIEFING DETAIL
        # ===================================================================
        if briefing.yesterday_recap and "No significant" not in briefing.yesterday_recap:
            self._layout.addSpacing(8)
            recap_card = QFrame()
            recap_card.setStyleSheet("""
                QFrame {
                    background: #0a0a12;
                    border: 1px solid #1a1a2a;
                    border-radius: 8px;
                    padding: 12px 16px;
                }
            """)
            r_layout = QVBoxLayout(recap_card)
            r_layout.setSpacing(2)
            r_title = QLabel("RECENT ACTIVITY")
            r_title.setStyleSheet("color: #505060; font-size: 10px; letter-spacing: 1.5px;")
            r_layout.addWidget(r_title)

            for line in briefing.yesterday_recap.split("\n"):
                r_line = QLabel(line)
                r_line.setStyleSheet("color: #9090a0; font-size: 12px;")
                r_layout.addWidget(r_line)

            self._layout.addWidget(recap_card)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
