from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QDialog,
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor

from ...experience.models.explain import Explanation


class ExplainPopup(QDialog):
    """Popup untuk menampilkan penjelasan."""

    def __init__(self, explanation, parent=None):
        super().__init__(parent)
        self.explanation = explanation
        self.setWindowTitle("Explanation")
        self.setMinimumSize(500, 400)
        self.setStyleSheet("background: #0a0a0f; color: #e0e0e0;")
        self._init_ui()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel(self.explanation.title)
        title.setStyleSheet("font-size: 18px; font-weight: bold; color: #e0e0e0;")
        layout.addWidget(title)

        # Severity
        colors = {
            "info": "#a0a0b0",
            "warning": "#e0c06a",
            "error": "#e06a6a",
            "critical": "#ff4444",
        }
        severity_label = QLabel("Severity: {}".format(
            self.explanation.severity.value.upper()
        ))
        severity_label.setStyleSheet(
            "color: {};".format(
                colors.get(self.explanation.severity.value, "#a0a0b0")
            )
        )
        layout.addWidget(severity_label)

        # Why
        why_label = QLabel("Why?")
        why_label.setStyleSheet("font-weight: bold; color: #c0c0c0; margin-top: 8px;")
        layout.addWidget(why_label)

        why_text = QLabel(self.explanation.why)
        why_text.setWordWrap(True)
        why_text.setStyleSheet("color: #a0a0b0; padding: 4px 0;")
        layout.addWidget(why_text)

        # Impact
        if self.explanation.impact:
            impact_label = QLabel("Impact:")
            impact_label.setStyleSheet("font-weight: bold; color: #c0c0c0; margin-top: 8px;")
            layout.addWidget(impact_label)

            impact_text = QLabel(self.explanation.impact.description)
            impact_text.setWordWrap(True)
            impact_text.setStyleSheet("color: #a0a0b0; padding: 4px 0;")
            layout.addWidget(impact_text)

        # Recommendation
        if self.explanation.recommendation:
            rec_label = QLabel("Recommendation:")
            rec_label.setStyleSheet("font-weight: bold; color: #c0c0c0; margin-top: 8px;")
            layout.addWidget(rec_label)

            rec_text = QLabel(self.explanation.recommendation.description)
            rec_text.setWordWrap(True)
            rec_text.setStyleSheet("color: #6aaae0; padding: 4px 0;")
            layout.addWidget(rec_text)

        # Evidence
        evidence_label = QLabel("Evidence:")
        evidence_label.setStyleSheet("font-weight: bold; color: #c0c0c0; margin-top: 8px;")
        layout.addWidget(evidence_label)

        for ev in self.explanation.evidence[:3]:
            ev_text = QLabel("\u2022 {}...".format(ev.description[:100]))
            ev_text.setWordWrap(True)
            ev_text.setStyleSheet("color: #888; font-size: 12px; padding: 2px 8px;")
            layout.addWidget(ev_text)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #2a4a6a;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                color: #fff;
                margin-top: 16px;
            }
            QPushButton:hover { background: #3a5a7a; }
        """)
        close_btn.clicked.connect(self.accept)
        layout.addWidget(close_btn)

        self.setLayout(layout)
