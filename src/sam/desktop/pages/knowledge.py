"""
Knowledge Page v4.0 — Conversation-powered.
History Page v4.0 — Cerita operasional dari Conversation.
Settings Page v4.0 — Pengaturan dari Conversation.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGroupBox, QFormLayout, QPushButton,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ...operations.conversation_api import Conversation


# ============================================================================
# KNOWLEDGE — Things SAM Learned
# ============================================================================

class KnowledgePage(QWidget):
    def __init__(self, conversation: Conversation):
        super().__init__()
        self.conversation = conversation
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setStyleSheet("background: transparent; padding: 24px 24px 8px 24px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Things SAM Learned")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)

        sub = QLabel("Knowledge gathered from operations.")
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
        root.addWidget(scroll)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(15000)
        self.refresh()

    def refresh(self):
        try:
            # DARI Conversation — explain() untuk insight
            answer = self.conversation.answer("What did SAM learn?")
            self._render(answer)
        except Exception:
            pass

    def _render(self, answer):
        self._clear()

        # Gunakan sections + predictions sebagai knowledge
        items = []
        if answer.sections:
            for label, text in answer.sections[:10]:
                items.append({"title": label, "details": text[:100], "severity": "info"})
        if answer.predictions:
            for p in answer.predictions[:3]:
                items.append({"title": p[:80], "details": "", "severity": "recommendation"})

        if not items:
            empty = QLabel("SAM has not learned anything yet. As SAM operates, it will collect patterns, incidents and lessons.")
            empty.setStyleSheet("color: #606070; font-size: 14px; padding: 24px;")
            empty.setWordWrap(True)
            self._layout.addWidget(empty)
            self._layout.addStretch()
            return

        for item in items:
            severity = item.get("severity", "info")
            color_map = {
                "recommendation": "#6aaae0",
                "warning": "#e0c06a",
            }
            color = color_map.get(severity, "#a0a0b0")
            icon_map = {
                "recommendation": "\U0001f4a1",
                "warning": "\u26a0\ufe0f",
            }
            icon = icon_map.get(severity, "\U0001f4cc")

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
            c_layout.setSpacing(4)

            row = QHBoxLayout()
            row.setSpacing(8)
            icon_w = QLabel(icon)
            icon_w.setStyleSheet("font-size: 14px;")
            row.addWidget(icon_w)

            text = QLabel(item["title"])
            text.setStyleSheet("color: {}; font-size: 13px;".format(color))
            text.setWordWrap(True)
            row.addWidget(text, 1)
            c_layout.addLayout(row)

            if item.get("details"):
                dt = QLabel(item["details"])
                dt.setStyleSheet("color: #606070; font-size: 11px; padding-left: 22px;")
                c_layout.addWidget(dt)

            self._layout.addWidget(card)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ============================================================================
# HISTORY — Cerita operasional
# ============================================================================

class HistoryPage(QWidget):
    def __init__(self, conversation: Conversation):
        super().__init__()
        self.conversation = conversation
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setStyleSheet("background: transparent; padding: 24px 24px 8px 24px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("History")
        title.setStyleSheet("font-size: 22px; font-weight: bold; color: #e0e0e0;")
        h_layout.addWidget(title)
        sub = QLabel("What happened recently.")
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
        self._layout.setSpacing(4)

        scroll.setWidget(self.content)
        root.addWidget(scroll)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(15000)
        self.refresh()

    def refresh(self):
        try:
            # DARI Conversation — timeline()
            answer = self.conversation.timeline()
            self._render(answer)
        except Exception:
            pass

    def _render(self, answer):
        self._clear()

        if not answer.sections and not answer.stories:
            empty = QLabel("No history yet. Once SAM completes operations, activity summaries will appear here.")
            empty.setStyleSheet("color: #606070; font-size: 14px; padding: 24px;")
            empty.setWordWrap(True)
            self._layout.addWidget(empty)
            self._layout.addStretch()
            return

        # Stories
        for story in (answer.stories or [])[:7]:
            # Day label
            label_container = QWidget()
            label_container.setStyleSheet("background: transparent;")
            l_layout = QHBoxLayout(label_container)
            l_layout.setContentsMargins(0, 12, 0, 4)
            l_layout.setSpacing(12)

            label = "Event" if len(story) > 40 else story.upper()
            label_w = QLabel(label)
            label_w.setStyleSheet("""
                color: #606070;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 1.5px;
            """)
            l_layout.addWidget(label_w)

            line = QFrame()
            line.setFrameShape(QFrame.HLine)
            line.setStyleSheet("color: #1a1a2a; margin-top: 2px;")
            l_layout.addWidget(line, 1)

            self._layout.addWidget(label_container)

            # Items dari sections
            for section_label, section_text in (answer.sections or [])[:10]:
                e_card = QFrame()
                e_card.setStyleSheet("""
                    QFrame {
                        background: transparent;
                        border: none;
                        padding: 3px 0;
                    }
                    QFrame:hover {
                        background: #0d0d18;
                        border-radius: 4px;
                    }
                """)
                e_layout = QHBoxLayout(e_card)
                e_layout.setContentsMargins(12, 2, 12, 2)
                e_layout.setSpacing(8)

                bullet = QLabel("\u2022")
                bullet.setStyleSheet("color: #404060; font-size: 14px;")
                e_layout.addWidget(bullet)

                e_text = QLabel(section_label)
                e_text.setStyleSheet("color: #b0b0c0; font-size: 13px;")
                e_text.setWordWrap(True)
                e_layout.addWidget(e_text, 1)

                self._layout.addWidget(e_card)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ============================================================================
# SETTINGS — Kelompok manusia
# ============================================================================

class SettingsPage(QWidget):
    def __init__(self, conversation: Conversation):
        super().__init__()
        self.conversation = conversation
        self._init_ui()

    def _init_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)

        header = QWidget()
        header.setStyleSheet("background: transparent; padding: 24px 24px 8px 24px;")
        h_layout = QVBoxLayout(header)
        h_layout.setContentsMargins(0, 0, 0, 0)
        title = QLabel("Settings")
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
        self._layout.setSpacing(12)

        scroll.setWidget(self.content)
        root.addWidget(scroll)
        self.refresh()

    def refresh(self):
        try:
            # DARI Conversation — technical details
            answer = self.conversation.technical_details()
            # Juga health untuk mendapat konfigurasi
            health = self.conversation.health()
            self._render(answer, health)
        except Exception:
            pass

    def _render(self, answer, health):
        self._clear()

        # Build groups from answer + health
        groups = [
            ("System", {
                "Label": answer.title or "SAM",
                "Status": health.title or "Healthy",
            }),
            ("Conversation", {
                "Intent": answer.intent or "technical",
                "Severity": health.severity or "information",
            }),
        ]

        # Technical details
        if answer.details:
            groups.append(("Technical Details", {
                "Description": answer.details[:200],
            }))

        for group in groups:
            name, settings = group
            gb = QGroupBox(name)
            gb.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #1a1a2a;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 16px;
                    padding-bottom: 8px;
                    font-size: 14px;
                    color: #e0e0e0;
                    font-weight: 500;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 8px;
                }
            """)

            form = QFormLayout()
            form.setSpacing(6)
            form.setContentsMargins(16, 8, 16, 8)

            for key, value in settings.items():
                label = QLabel(key)
                label.setStyleSheet("color: #a0a0b0; font-size: 12px;")

                val_color = "#e0e0e0"
                if isinstance(value, str):
                    v_lower = value.lower()
                    if v_lower in ("true", "enabled", "autonomous"):
                        val_color = "#4ae04a"
                    elif v_lower in ("false", "disabled"):
                        val_color = "#e06a6a"
                    elif v_lower in ("healthy", "normal", "information"):
                        val_color = "#4ae04a"

                val = QLabel(str(value))
                val.setStyleSheet("color: {}; font-size: 13px;".format(val_color))

                form.addRow(label, val)

            gb.setLayout(form)
            self._layout.addWidget(gb)

        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
