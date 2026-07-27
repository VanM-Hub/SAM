"""
Home Page v3.1 — Ringkasan operasional.

Dapat dibaca < 5 detik.
Menjawab:
- Apakah sistem sehat?
- Apa yang terjadi?
- Apakah perlu tindakan?
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QColor

from ...experience.engine import ExperienceEngine, SystemStatus


class HomePage(QWidget):
    def __init__(self, experience):
        super().__init__()
        self.experience = experience
        self._init_ui()

    def _init_ui(self):
        # Root layout
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

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
            self._render(model)
        except Exception:
            pass

    def _render(self, model):
        self._clear()

        # ===================================================================
        # 1. STATUS — big, bold, visible instantly
        # ===================================================================
        if model.health.status == SystemStatus.HEALTHY:
            icon = "\u2705"
            color = "#4ae04a"
            bg_card = """
                QFrame {
                    background: #0a1a0a;
                    border: 1px solid #1a3a1a;
                    border-radius: 12px;
                    padding: 20px;
                }
            """
        elif model.health.status == SystemStatus.PROBLEM:
            icon = "\u274c"
            color = "#e06a6a"
            bg_card = """
                QFrame {
                    background: #1a0a0a;
                    border: 1px solid #3a1a1a;
                    border-radius: 12px;
                    padding: 20px;
                }
            """
        elif model.health.status == SystemStatus.RECOVERING:
            icon = "\U0001f504"
            color = "#e0c06a"
            bg_card = """
                QFrame {
                    background: #1a1a0a;
                    border: 1px solid #3a3a1a;
                    border-radius: 12px;
                    padding: 20px;
                }
            """
        else:
            icon = "\U0001f9e0"
            color = "#6aaae0"
            bg_card = """
                QFrame {
                    background: #0a0a1a;
                    border: 1px solid #1a1a3a;
                    border-radius: 12px;
                    padding: 20px;
                }
            """

        status_card = QFrame()
        status_card.setStyleSheet(bg_card)
        s_layout = QVBoxLayout(status_card)
        s_layout.setSpacing(4)

        # Main status
        main_line = QHBoxLayout()
        icon_label = QLabel(icon)
        icon_label.setStyleSheet("font-size: 28px;")
        main_line.addWidget(icon_label)

        msg_label = QLabel(model.health.message)
        msg_label.setStyleSheet("color: {}; font-size: 22px; font-weight: bold;".format(color))
        main_line.addWidget(msg_label)
        main_line.addStretch()
        s_layout.addLayout(main_line)

        # Detail
        detail_label = QLabel(model.health.detail)
        detail_label.setStyleSheet("color: #a0a0b0; font-size: 13px; padding-left: 40px;")
        s_layout.addWidget(detail_label)

        self._layout.addWidget(status_card)
        self._layout.addSpacing(24)

        # ===================================================================
        # 2. PURPOSE + CURRENT ACTIVITY (side by side)
        # ===================================================================
        row2 = QHBoxLayout()
        row2.setSpacing(16)

        # Purpose card
        purpose_card = QFrame()
        purpose_card.setStyleSheet("""
            QFrame {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        p_layout = QVBoxLayout(purpose_card)
        p_layout.setSpacing(4)
        p_title = QLabel("PURPOSE")
        p_title.setStyleSheet("color: #606070; font-size: 10px; letter-spacing: 1.5px;")
        p_layout.addWidget(p_title)
        p_value = QLabel(model.purpose.name)
        p_value.setStyleSheet("color: #e0e0e0; font-size: 15px;")
        p_layout.addWidget(p_value)
        row2.addWidget(purpose_card)

        # Activity card
        activity_card = QFrame()
        activity_card.setStyleSheet("""
            QFrame {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        a_layout = QVBoxLayout(activity_card)
        a_layout.setSpacing(4)
        a_title = QLabel("CURRENT ACTIVITY")
        a_title.setStyleSheet("color: #606070; font-size: 10px; letter-spacing: 1.5px;")
        a_layout.addWidget(a_title)
        a_value = QLabel(model.current_activity.title)
        a_value.setStyleSheet("color: #c0c0d0; font-size: 14px;")
        a_layout.addWidget(a_value)
        row2.addWidget(activity_card)

        self._layout.addLayout(row2)
        self._layout.addSpacing(16)

        # ===================================================================
        # 3. ATTENTION
        # ===================================================================
        attention_card = QFrame()
        if model.attention.needs_attention:
            att_color = "#e0c06a"
            att_bg = "background: #1a1a0a; border: 1px solid #3a3a1a;"
            att_icon = "\u26a0\ufe0f"
        else:
            att_color = "#4ae04a"
            att_bg = "background: #0a0a12; border: 1px solid #1a1a2a;"
            att_icon = "\u2705"

        attention_card.setStyleSheet("""
            QFrame {{
                {} border-radius: 10px;
                padding: 16px;
            }}
        """.format(att_bg))
        att_layout = QVBoxLayout(attention_card)
        att_layout.setSpacing(2)

        att_header = QHBoxLayout()
        att_title = QLabel("ATTENTION")
        att_title.setStyleSheet("color: #606070; font-size: 10px; letter-spacing: 1.5px;")
        att_header.addWidget(att_title)
        att_header.addStretch()
        att_layout.addLayout(att_header)

        att_msg = QLabel("{}  {}".format(att_icon, model.attention.message))
        att_msg.setStyleSheet("color: {}; font-size: 14px;".format(att_color))
        att_layout.addWidget(att_msg)

        if model.attention.reason:
            att_reason = QLabel("    Reason: {}".format(model.attention.reason))
            att_reason.setStyleSheet("color: #808090; font-size: 12px;")
            att_layout.addWidget(att_reason)

        self._layout.addWidget(attention_card)
        self._layout.addSpacing(16)

        # ===================================================================
        # 4. RECOMMENDATIONS
        # ===================================================================
        rec_card = QFrame()
        rec_card.setStyleSheet("""
            QFrame {
                background: #0a0a12;
                border: 1px solid #1a1a2a;
                border-radius: 10px;
                padding: 16px;
            }
        """)
        rec_layout = QVBoxLayout(rec_card)
        rec_layout.setSpacing(4)

        rec_title = QLabel("RECOMMENDATIONS")
        rec_title.setStyleSheet("color: #606070; font-size: 10px; letter-spacing: 1.5px;")
        rec_layout.addWidget(rec_title)

        has_content = False
        for r in model.recommendations:
            if r.message and r.message != "Nothing recommended.":
                has_content = True
                rec_item = QLabel("\U0001f4a1  {}".format(r.message))
                rec_item.setStyleSheet("color: #6aaae0; font-size: 13px;")
                rec_item.setWordWrap(True)
                rec_layout.addWidget(rec_item)
                if r.confidence:
                    conf = QLabel("   Confidence: {:.0f}%".format(r.confidence * 100))
                    conf.setStyleSheet("color: #606070; font-size: 11px;")
                    rec_layout.addWidget(conf)

        if not has_content:
            rec_empty = QLabel("\U0001f4a1  Nothing recommended.")
            rec_empty.setStyleSheet("color: #606070; font-size: 13px;")
            rec_layout.addWidget(rec_empty)

        self._layout.addWidget(rec_card)

        # Recent activity log
        if model.current_activity.activity_log:
            self._layout.addSpacing(16)
            log_card = QFrame()
            log_card.setStyleSheet("""
                QFrame {
                    background: #0a0a12;
                    border: 1px solid #1a1a2a;
                    border-radius: 10px;
                    padding: 16px;
                }
            """)
            log_layout = QVBoxLayout(log_card)
            log_layout.setSpacing(4)
            log_title = QLabel("RECENT ACTIVITY")
            log_title.setStyleSheet("color: #606070; font-size: 10px; letter-spacing: 1.5px;")
            log_layout.addWidget(log_title)

            for item in model.current_activity.activity_log[:5]:
                row = QLabel("{}  {}".format(item.time, item.description))
                row.setStyleSheet("color: #9090a0; font-size: 12px;")
                log_layout.addWidget(row)

            self._layout.addWidget(log_card)

        # Spacer
        self._layout.addStretch()

    def _clear(self):
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
