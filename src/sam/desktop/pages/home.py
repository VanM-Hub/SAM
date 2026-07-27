"""
Home Page v3.2 — Satu produk.

Setiap halaman menjawab satu pertanyaan manusia.
Home: "What is happening?"
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea,
)
from PySide6.QtCore import Qt, QTimer

from ...experience.engine import ExperienceEngine
from ..widgets import StatusCard, RecommendationCard, AttentionBanner
from ..context import ExperienceContextBuilder


class HomePage(QWidget):
    """Home — 'What is happening?'"""

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

        # Status card — reusable
        self._status_card = StatusCard()
        self._layout.addWidget(self._status_card)

        # Attention banner
        self._attention_banner = AttentionBanner()
        self._attention_banner.action_clicked.connect(lambda a: self._switch_activity())
        self._layout.addWidget(self._attention_banner)
        self._attention_banner.hide()

        # Recommendation placeholder
        self._rec_layout = QVBoxLayout()
        self._rec_layout.setSpacing(8)
        self._layout.addLayout(self._rec_layout)

        # Narrative — briefing
        self._briefing_card = QFrame()
        self._briefing_card.setStyleSheet("""
            QFrame { background: #0a0a12; border: 1px solid #1a1a2a;
                     border-radius: 10px; padding: 16px; }
        """)
        self._briefing_layout = QVBoxLayout(self._briefing_card)
        self._briefing_layout.setSpacing(4)
        self._layout.addWidget(self._briefing_card)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(5000)
        self.refresh()

    def _switch_activity(self):
        """Switch ke Activity page (dipanggil dari parent)."""
        parent = self.parent()
        if parent and hasattr(parent, 'switch_page'):
            parent.switch_page(1)

    def update_context(self, ctx):
        """Update dari ExperienceContext."""
        self._status_card.update_from_context(ctx)
        self._attention_banner.update_from_context(ctx)

    def refresh(self):
        try:
            ctx = self._ctx_builder.build()
            self._status_card.update_from_context(ctx)
            self._attention_banner.update_from_context(ctx)

            # Clean rekomendasi
            self._clear_recs()

            # Recommendations — dari narrative
            narrative = self.experience.build_narrative_home()
            if narrative and narrative.supporting:
                added = False
                for n in narrative.supporting:
                    if n.importance.value in ("attention", "information"):
                        rec = RecommendationCard()
                        rec.set_data(
                            reason=n.title,
                            recommendation=n.recommended_action or n.summary,
                            impact=n.estimated_impact or "",
                        )
                        self._rec_layout.addWidget(rec)
                        added = True
                if added:
                    self._rec_layout.parent().show()
            else:
                # Empty state narrative
                self._rec_layout.parent().hide()

            # Briefing
            self._clear_briefing()
            try:
                brief = self.experience.build_daily_briefing()
                lines = [brief.greeting, brief.health_summary, brief.action_summary]
                if brief.schedule:
                    lines.append("Today's scheduled work:")
                    lines.extend("  " + s for s in brief.schedule)
                for line in lines:
                    l = QLabel(line)
                    l.setStyleSheet("color: #c0c0d0; font-size: 13px;")
                    l.setWordWrap(True)
                    self._briefing_layout.addWidget(l)
            except Exception:
                pass

        except Exception:
            pass

    def _clear_recs(self):
        while self._rec_layout.count():
            item = self._rec_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _clear_briefing(self):
        while self._briefing_layout.count():
            item = self._briefing_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
