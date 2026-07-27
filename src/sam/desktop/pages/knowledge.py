"""
Knowledge Page — Things SAM Learned.
History Page — Cerita operasional.
Settings Page — Pengaturan dalam kelompok manusia.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGroupBox, QFormLayout,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

from ...experience.engine import ExperienceEngine


# ============================================================================
# KNOWLEDGE
# ============================================================================

class KnowledgePage(QWidget):
    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Things SAM Learned")
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
        self.content_layout.setSpacing(8)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(15000)
        self.refresh()

    def refresh(self):
        try:
            model = self.experience.build_knowledge()
            self._render(model)
        except Exception:
            pass

    def _render(self, model):
        self._clear()

        for item in model.items[:20]:
            # Determine color
            if item.severity == "recommendation":
                color = "#6aaae0"
                icon = "\U0001f4a1"
            elif item.severity == "warning":
                color = "#e0c06a"
                icon = "\u26a0\ufe0f"
            else:
                color = "#a0a0b0"
                icon = "\U0001f4cc"

            card = QFrame()
            card.setStyleSheet("""
                QFrame {
                    background: #0d0d16;
                    border: 1px solid #1a1a2a;
                    border-radius: 6px;
                    padding: 10px 14px;
                }
            """)
            card_layout = QVBoxLayout(card)
            card_layout.setSpacing(2)

            row = QLabel("{}  {}".format(icon, item.title))
            row.setStyleSheet("color: {}; font-size: 13px;".format(color))
            row.setWordWrap(True)
            card_layout.addWidget(row)

            if item.confidence:
                conf = QLabel("   Confidence: {:.0f}%".format(item.confidence * 100))
                conf.setStyleSheet("color: #606070; font-size: 11px;")
                card_layout.addWidget(conf)

            if item.timestamp:
                ts = QLabel("   {}".format(item.timestamp))
                ts.setStyleSheet("color: #505060; font-size: 10px;")
                card_layout.addWidget(ts)

            self.content_layout.addWidget(card)

    def _clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ============================================================================
# HISTORY
# ============================================================================

class HistoryPage(QWidget):
    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("History")
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
        self.content_layout.setSpacing(4)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(15000)
        self.refresh()

    def refresh(self):
        try:
            model = self.experience.build_history()
            self._render(model)
        except Exception:
            pass

    def _render(self, model):
        self._clear()

        for story in model.stories[:7]:
            # Label
            label = QLabel(story.label)
            label.setStyleSheet("""
                color: #808090;
                font-size: 12px;
                font-weight: bold;
                letter-spacing: 1px;
                padding: 8px 0 4px 0;
            """)
            self.content_layout.addWidget(label)

            # Events
            for event in story.events[:10]:
                e = QLabel("  \u2022  {}".format(event))
                e.setStyleSheet("color: #b0b0c0; font-size: 13px; padding: 2px 0;")
                self.content_layout.addWidget(e)

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


# ============================================================================
# SETTINGS
# ============================================================================

class SettingsPage(QWidget):
    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(24, 24, 24, 24)

        title = QLabel("Settings")
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
        self.content_layout.setSpacing(12)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)
        self.setLayout(layout)

        self.refresh()

    def refresh(self):
        try:
            model = self.experience.build_settings()
            self._render(model)
        except Exception:
            pass

    def _render(self, model):
        self._clear()

        for group in model.groups:
            gb = QGroupBox(group.name)
            gb.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #1a1a2a;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 16px;
                    font-size: 14px;
                    color: #e0e0e0;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 14px;
                    padding: 0 8px;
                }
            """)
            form = QFormLayout()
            form.setSpacing(6)
            form.setContentsMargins(16, 12, 16, 12)

            for key, value in group.settings.items():
                label = QLabel(key)
                label.setStyleSheet("color: #a0a0b0;")
                val = QLabel(value)
                val.setStyleSheet("color: #e0e0e0;")
                form.addRow(label, val)

            gb.setLayout(form)
            self.content_layout.addWidget(gb)

    def _clear(self):
        while self.content_layout.count():
            item = self.content_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
