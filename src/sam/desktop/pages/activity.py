"""
Activity Page — Human Timeline, bukan log.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QLabel, QFrame, QScrollArea,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ...experience.engine import ExperienceEngine


class ActivityPage(QWidget):
    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)

        # Header
        title = QLabel("Activity")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0; margin-bottom: 8px;")
        layout.addWidget(title)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(0)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(10000)
        self.refresh()

    def refresh(self):
        try:
            model = self.experience.build_activity()
            self._render(model)
        except Exception:
            pass

    def _render(self, model):
        self._clear()

        for group in model.groups[:7]:
            # Day header
            header = QLabel(group.label)
            header.setStyleSheet("""
                color: #808090;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 12px 0 4px 0;
            """)
            self.content_layout.addWidget(header)

            # Entries
            for entry in group.entries[:10]:
                container = QFrame()
                container.setStyleSheet("""
                    QFrame {
                        background: transparent;
                        border: none;
                        padding: 2px 0;
                    }
                    QFrame:hover {
                        background: #0f0f18;
                        border-radius: 4px;
                    }
                """)
                entry_layout = QVBoxLayout(container)
                entry_layout.setContentsMargins(8, 4, 8, 4)
                entry_layout.setSpacing(0)

                # Time + Description
                row = QLabel("{}  {}".format(entry.time, entry.description))
                row.setStyleSheet("color: #c0c0d0; font-size: 13px;")
                entry_layout.addWidget(row)

                # Details (hanya muncul jika ada)
                if entry.details:
                    details = QLabel("     {}".format(entry.details))
                    details.setStyleSheet("color: #606070; font-size: 11px;")
                    entry_layout.addWidget(details)

                self.content_layout.addWidget(container)

            # Separator
            sep = QFrame()
            sep.setFrameShape(QFrame.HLine)
            sep.setStyleSheet("color: #12121a; margin: 4px 0;")
            self.content_layout.addWidget(sep)

    def _clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
