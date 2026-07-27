"""
Activity Page v3.1 — Human Timeline.

Bukan log.
Bukan audit.
Timeline cerita.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QLineEdit,
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
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # Header
        header = QWidget()
        header.setStyleSheet("background: transparent; padding: 24px 24px 8px 24px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)

        title = QLabel("Activity")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Filter activity...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 8px;
                padding: 8px 14px;
                color: #e0e0e0;
                font-size: 12px;
                max-width: 300px;
            }
            QLineEdit:focus {
                border: 1px solid #2a2a4a;
            }
        """)
        self.search_input.textChanged.connect(self._on_search)
        h_layout.addWidget(self.search_input)

        root.addWidget(header)

        # Scroll
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
        self._layout.setSpacing(0)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

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

    def _on_search(self):
        self.refresh()

    def _render(self, model):
        self._clear()

        for group in model.groups[:7]:
            # Day header with horizontal line
            header_container = QWidget()
            header_container.setStyleSheet("background: transparent;")
            h_layout = QHBoxLayout(header_container)
            h_layout.setContentsMargins(0, 16, 0, 4)
            h_layout.setSpacing(12)

            day_label = QLabel(group.label.upper())
            day_label.setStyleSheet("""
                color: #606070;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1.5px;
            """)
            h_layout.addWidget(day_label)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("color: #1a1a2a; margin-top: 2px;")
            h_layout.addWidget(line, 1)

            self._layout.addWidget(header_container)

            # Timeline entries
            for entry in group.entries[:15]:
                entry_container = QFrame()
                entry_container.setStyleSheet("""
                    QFrame {
                        background: transparent;
                        border: none;
                        padding: 4px 0;
                    }
                    QFrame:hover {
                        background: #0d0d18;
                        border-radius: 6px;
                    }
                """)

                e_layout = QHBoxLayout(entry_container)
                e_layout.setContentsMargins(12, 4, 12, 4)
                e_layout.setSpacing(12)

                # Timeline dot
                dot = QLabel("\u2022")
                dot.setStyleSheet("color: #404060; font-size: 18px;")
                dot.setFixedWidth(12)
                e_layout.addWidget(dot)

                # Time
                time_label = QLabel(entry.time)
                time_label.setStyleSheet("color: #606080; font-size: 12px; font-weight: 500;")
                time_label.setFixedWidth(40)
                e_layout.addWidget(time_label)

                # Description
                desc_label = QLabel(entry.description)
                desc_label.setStyleSheet("color: #c0c0d0; font-size: 13px;")
                desc_label.setWordWrap(True)
                e_layout.addWidget(desc_label, 1)

                self._layout.addWidget(entry_container)

        if not model.groups:
            empty = QLabel("No activity recorded yet.")
            empty.setStyleSheet("color: #606070; font-size: 14px; padding: 24px;")
            self._layout.addWidget(empty)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
