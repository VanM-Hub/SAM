"""
Activity Page v3.2 — Satu produk.

'What happened?'
Menggunakan TimelineWidget reusable.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea, QLineEdit,
)
from PySide6.QtCore import Qt, QTimer

from ...experience.engine import ExperienceEngine
from ..widgets import TimelineWidget, StatusCard
from ..context import ExperienceContextBuilder


class ActivityPage(QWidget):
    """Activity — 'What happened?'"""

    def __init__(self, experience, ctx_builder):
        super().__init__()
        self.experience = experience
        self._ctx_builder = ctx_builder
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
            model = self.experience.build_activity()
            query = self.search_input.text().lower()

            groups = []
            for g in model.groups[:7]:
                entries = [e for e in g.entries[:15] if not query or query in e.description.lower()]
                if entries:
                    groups.append((g.label, entries))

            self._timeline.set_groups(groups)
        except Exception:
            pass
