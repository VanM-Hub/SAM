"""
Shared widgets — SAM Operations Console.

Semua halaman pakai widget yang sama.
Tidak ada duplikasi rendering logic.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QPushButton, QLineEdit,
)
from PySide6.QtCore import Qt, QTimer, Signal
from PySide6.QtGui import QFont

from .context import HumanTimeFormatter


# ============================================================================
# StatusCard — digunakan oleh Home, Settings, Activity, Work
# ============================================================================

class StatusCard(QFrame):
    """Status ringkas. Satu baris. Bisa dibaca dalam 2 detik."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #08080f;
                border: 1px solid #141422;
                border-radius: 12px;
                padding: 20px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(4)

        # Icon + label
        self._header = QHBoxLayout()
        self._icon = QLabel()
        self._icon.setStyleSheet("font-size: 20px;")
        self._header.addWidget(self._icon)

        self._label = QLabel()
        self._label.setStyleSheet("font-size: 18px; font-weight: bold;")
        self._header.addWidget(self._label)
        self._header.addStretch()
        layout.addLayout(self._header)

        # Detail
        self._detail = QLabel()
        self._detail.setStyleSheet("color: #808090; font-size: 12px; padding-left: 30px;")
        self._detail.setWordWrap(True)
        layout.addWidget(self._detail)

    def update_from_context(self, ctx):
        """Update dari ExperienceContext."""
        icon_map = {
            "Healthy": "\u2705",
            "Attention": "\u26a0\ufe0f",
            "Problem": "\u274c",
            "Recovering": "\U0001f504",
            "Learning": "\U0001f9e0",
            "Unknown": "\u2753",
        }
        self._icon.setText(icon_map.get(ctx.status_label, "\u2753"))
        self._label.setText(ctx.status_label)
        self._label.setStyleSheet(
            "color: {}; font-size: 18px; font-weight: bold;".format(ctx.status_color)
        )
        self._detail.setText(ctx.status_detail)

    def set_human_focus(self, focus_message: str, focus_detail: str,
                        action_message: str, color: str = "#e0e0e0"):
        """Set satu fokus — bukan dashboard.

        Hanya satu pesan besar yang dilihat user.
        """
        self._icon.setText("")
        self._label.setText(focus_message)
        self._label.setStyleSheet(
            "color: {}; font-size: 22px; font-weight: bold;".format(color)
        )
        if focus_detail:
            self._detail.setText(focus_detail)
        else:
            self._detail.setText("")


# ============================================================================
# AttentionBanner — bukan modal dialog
# ============================================================================

class AttentionBanner(QFrame):
    """Banner yang muncul jika ada yang perlu perhatian."""

    action_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #1a1a0a;
                border: 1px solid #3a3a1a;
                border-radius: 8px;
                padding: 10px 16px;
            }
        """)
        layout = QHBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 8, 16, 8)

        self._icon = QLabel("\u26a0\ufe0f")
        self._icon.setStyleSheet("font-size: 16px;")
        layout.addWidget(self._icon)

        self._message = QLabel()
        self._message.setStyleSheet("color: #e0c06a; font-size: 13px;")
        layout.addWidget(self._message, 1)

        self._action_btn = QPushButton("View")
        self._action_btn.setStyleSheet("""
            QPushButton {
                background: #2a4a2a;
                border: none;
                border-radius: 4px;
                padding: 4px 12px;
                color: #fff;
                font-size: 11px;
            }
            QPushButton:hover { background: #3a5a3a; }
        """)
        self._action_btn.clicked.connect(lambda: self.action_clicked.emit("view"))
        layout.addWidget(self._action_btn)

        self._later_btn = QPushButton("Later")
        self._later_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: 1px solid #3a3a1a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #808070;
                font-size: 11px;
            }
            QPushButton:hover { background: #2a2a0a; }
        """)
        self._later_btn.clicked.connect(lambda: self.action_clicked.emit("later"))
        layout.addWidget(self._later_btn)

        self.hide()

    def update_from_context(self, ctx):
        if ctx.needs_attention:
            self._message.setText(ctx.attention_message or "Action required.")
            self.show()
        else:
            self.hide()


# ============================================================================
# RecommendationCard — reason + recommendation + impact + button
# ============================================================================

class RecommendationCard(QFrame):
    action_clicked = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 10px;
                padding: 14px;
            }
        """)
        layout = QVBoxLayout(self)
        layout.setSpacing(6)

        # Header
        header = QHBoxLayout()
        icon = QLabel("\U0001f4a1")
        icon.setStyleSheet("font-size: 14px;")
        header.addWidget(icon)

        self._reason = QLabel()
        self._reason.setStyleSheet("color: #c0c0d0; font-size: 14px; font-weight: 500;")
        self._reason.setWordWrap(True)
        header.addWidget(self._reason, 1)
        layout.addLayout(header)

        # Recommendation
        self._recommendation = QLabel()
        self._recommendation.setStyleSheet("color: #6aaae0; font-size: 13px; padding-left: 20px;")
        self._recommendation.setWordWrap(True)
        layout.addWidget(self._recommendation)

        # Impact
        self._impact = QLabel()
        self._impact.setStyleSheet("color: #606070; font-size: 11px; padding-left: 20px;")
        layout.addWidget(self._impact)

        # Button
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self._btn = QPushButton("View Details")
        self._btn.setStyleSheet("""
            QPushButton {
                background: #1a1a2a;
                border: 1px solid #2a2a3a;
                border-radius: 4px;
                padding: 4px 12px;
                color: #a0a0b0;
                font-size: 11px;
            }
            QPushButton:hover { background: #2a2a3a; }
        """)
        self._btn.clicked.connect(lambda: self.action_clicked.emit("details"))
        btn_layout.addWidget(self._btn)
        layout.addLayout(btn_layout)

    def set_data(self, reason: str, recommendation: str, impact: str = ""):
        self._reason.setText(reason)
        self._recommendation.setText(recommendation)
        self._impact.setText(impact if impact else "")


# ============================================================================
# TimelineWidget — digunakan oleh Activity, History, Notification
# ============================================================================

class TimelineEntryWidget(QFrame):
    """Satu baris di timeline."""

    def __init__(self, time_text: str, description: str, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
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
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 3, 12, 3)
        layout.setSpacing(10)

        dot = QLabel("\u2022")
        dot.setStyleSheet("color: #404060; font-size: 16px;")
        dot.setFixedWidth(12)
        layout.addWidget(dot)

        time_l = QLabel(time_text)
        time_l.setStyleSheet("color: #505070; font-size: 12px; font-weight: 500;")
        time_l.setFixedWidth(42)
        layout.addWidget(time_l)

        desc_l = QLabel(description)
        desc_l.setStyleSheet("color: #c0c0d0; font-size: 13px;")
        desc_l.setWordWrap(True)
        layout.addWidget(desc_l, 1)


class TimelineGroupWidget(QFrame):
    """Satu grup timeline (Today/Yesterday/Date)."""

    def __init__(self, group_label: str, entries: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Label
        label_w = QWidget()
        l_layout = QHBoxLayout(label_w)
        l_layout.setContentsMargins(0, 16, 0, 4)
        l_layout.setSpacing(12)

        day_label = QLabel(group_label.upper())
        day_label.setStyleSheet("color: #606070; font-size: 11px; font-weight: bold; letter-spacing: 1.5px;")
        l_layout.addWidget(day_label)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #1a1a2a; margin-top: 2px;")
        l_layout.addWidget(line, 1)

        layout.addWidget(label_w)

        # Entries
        for entry in entries[:15]:
            time_text = getattr(entry, 'time', '')
            desc = getattr(entry, 'description', str(entry))
            ew = TimelineEntryWidget(time_text, desc)
            layout.addWidget(ew)


class TimelineWidget(QFrame):
    """Timeline reusable widget.

    Menerima list of groups (label + entries).
    Digunakan oleh: Activity, History, Notification.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("background: transparent;")
        self._layout = QVBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(0)

    def set_groups(self, groups: list):
        """Set grup timeline.

        Args:
            groups: list of (label, entries) tuples
        """
        self._clear()
        for label, entries in groups:
            gw = TimelineGroupWidget(label, entries)
            self._layout.addWidget(gw)
        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()


# ============================================================================
# SearchBar — Search Everywhere
# ============================================================================

class SearchBar(QWidget):
    """Global search. Bisa cari History, Knowledge, Activity, Work, Commands."""

    search_requested = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self._input = QLineEdit()
        self._input.setPlaceholderText("Search everywhere...  (Ctrl+K)")
        self._input.setStyleSheet("""
            QLineEdit {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 8px;
                padding: 8px 14px;
                color: #e0e0e0;
                font-size: 12px;
            }
            QLineEdit:focus {
                border: 1px solid #2a2a4a;
            }
        """)
        self._input.returnPressed.connect(self._search)
        layout.addWidget(self._input)

    def _search(self):
        query = self._input.text().strip()
        if query:
            self.search_requested.emit(query)

    def clear(self):
        self._input.clear()

