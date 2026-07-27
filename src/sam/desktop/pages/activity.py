"""
Activity Page v3.1 — Narrative Timeline.

Setiap baris adalah cerita, bukan log.
Group: Today / Yesterday / Earlier.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QPushButton, QLineEdit,
)
from PySide6.QtCore import Qt, QTimer

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

        header = QWidget()
        header.setStyleSheet("background: transparent; padding: 24px 24px 8px 24px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(8)

        title = QLabel("Activity")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)

        sub = QLabel("What happened — told in moments, not in logs.")
        sub.setStyleSheet("color: #606070; font-size: 12px; margin-top: 2px;")
        h_layout.addWidget(sub)

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
        self.search_input.textChanged.connect(self.refresh)
        h_layout.addWidget(self.search_input)

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
            narratives = self.experience.build_narrative_activity()
            self._render(model, narratives)
        except Exception:
            pass

    def _render(self, model, narratives):
        self._clear()

        query = self.search_input.text().lower()

        for group in model.groups[:7]:
            # Day label
            label_w = QWidget()
            label_w.setStyleSheet("background: transparent;")
            l_layout = QHBoxLayout(label_w)
            l_layout.setContentsMargins(0, 16, 0, 4)
            l_layout.setSpacing(12)

            day_label = QLabel(group.label.upper())
            day_label.setStyleSheet("""
                color: #606070;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1.5px;
            """)
            l_layout.addWidget(day_label)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("color: #1a1a2a; margin-top: 2px;")
            l_layout.addWidget(line, 1)

            self._layout.addWidget(label_w)

            # Entry narrative cards
            for entry in group.entries[:15]:
                desc = entry.description
                if query and query not in desc.lower():
                    continue

                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background: transparent;
                        border: none;
                        padding: 3px 0;
                    }
                    QFrame:hover {
                        background: #0d0d18;
                        border-radius: 6px;
                    }
                """)
                c_layout = QHBoxLayout(card)
                c_layout.setContentsMargins(12, 3, 12, 3)
                c_layout.setSpacing(10)

                # Dot
                dot = QLabel("\u2022")
                dot.setStyleSheet("color: #404060; font-size: 16px;")
                dot.setFixedWidth(12)
                c_layout.addWidget(dot)

                # Time
                time_l = QLabel(entry.time)
                time_l.setStyleSheet("color: #505070; font-size: 12px; font-weight: 500;")
                time_l.setFixedWidth(42)
                c_layout.addWidget(time_l)

                # Story — narrative description
                desc_l = QLabel(desc)
                desc_l.setStyleSheet("color: #c0c0d0; font-size: 13px;")
                desc_l.setWordWrap(True)
                c_layout.addWidget(desc_l, 1)

                self._layout.addWidget(card)

            # Narrative cards after each group
            for n in narratives:
                card = QFrame()
                card.setStyleSheet("""
                    QFrame {
                        background: #0a0a12;
                        border: 1px solid #1a1a2a;
                        border-radius: 8px;
                        padding: 10px 14px;
                        margin: 4px 0;
                    }
                    QFrame:hover {
                        border: 1px solid #2a2a3a;
                    }
                """)
                nc_layout = QHBoxLayout(card)
                nc_layout.setSpacing(8)

                icon = QLabel("\U0001f4cc")
                icon.setStyleSheet("font-size: 13px;")
                nc_layout.addWidget(icon)

                text = QLabel(n.summary)
                text.setStyleSheet("color: #a0a0b0; font-size: 12px;")
                text.setWordWrap(True)
                nc_layout.addWidget(text, 1)

                self._layout.addWidget(card)

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
