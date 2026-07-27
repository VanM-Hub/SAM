from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QStackedWidget, QFrame,
    QLineEdit, QScrollArea
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ...operations.engine.knowledge import KnowledgeEngine
from ...experience.models.knowledge import KnowledgeEntry, KnowledgeType
from ...telemetry.service import TelemetryService


class KnowledgePage(QWidget):
    """Halaman Knowledge untuk Desktop."""

    def __init__(self, telemetry, knowledge_store=None):
        super().__init__()
        self.telemetry = telemetry
        self.engine = KnowledgeEngine(telemetry, knowledge_store)
        self.current_model = None
        self._init_ui()
        self._start_refresh()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("\U0001f9e0 Knowledge & Insights")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0e0;")
        header.addWidget(title)
        header.addStretch()

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("\U0001f50d Search knowledge...")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background: #12121a;
                border: 1px solid #2a2a3a;
                border-radius: 6px;
                padding: 6px 12px;
                color: #e0e0e0;
                min-width: 200px;
            }
        """)
        self.search_input.returnPressed.connect(self._search)
        header.addWidget(self.search_input)

        refresh_btn = QPushButton("\U0001f504 Refresh")
        refresh_btn.setStyleSheet("""
            QPushButton {
                background: #2a4a6a;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                color: #fff;
            }
            QPushButton:hover { background: #3a5a7a; }
        """)
        refresh_btn.clicked.connect(self.refresh)
        header.addWidget(refresh_btn)
        layout.addLayout(header)

        # Split: Insights + Entries
        split = QHBoxLayout()

        # Left: Insights
        insight_widget = QFrame()
        insight_widget.setStyleSheet(
            "background: #12121a; border: 1px solid #2a2a3a; border-radius: 8px; padding: 12px;"
        )
        insight_layout = QVBoxLayout(insight_widget)
        insight_label = QLabel("\U0001f4a1 Insights")
        insight_label.setStyleSheet("font-weight: bold; color: #c0c0c0;")
        insight_layout.addWidget(insight_label)

        self.insight_list = QListWidget()
        self.insight_list.setStyleSheet("background: transparent; border: none;")
        insight_layout.addWidget(self.insight_list)
        split.addWidget(insight_widget, 1)

        # Right: Knowledge entries
        entry_widget = QFrame()
        entry_widget.setStyleSheet(
            "background: #12121a; border: 1px solid #2a2a3a; border-radius: 8px; padding: 12px;"
        )
        entry_layout = QVBoxLayout(entry_widget)
        entry_label = QLabel("\U0001f4da Knowledge")
        entry_label.setStyleSheet("font-weight: bold; color: #c0c0c0;")
        entry_layout.addWidget(entry_label)

        self.entry_list = QListWidget()
        self.entry_list.setStyleSheet("background: transparent; border: none;")
        entry_layout.addWidget(self.entry_list)
        split.addWidget(entry_widget, 2)

        layout.addLayout(split)
        self.setLayout(layout)

        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh)
        self.refresh_timer.start(15000)

    def _start_refresh(self):
        self.refresh()

    def refresh(self):
        try:
            self.current_model = self.engine.get_knowledge()
            self._render()
        except Exception:
            pass

    def _search(self):
        query = self.search_input.text().strip()
        if not query:
            self.refresh()
            return
        results = self.engine.search(query)
        self._render_results(results)

    def _render(self):
        if not self.current_model:
            return

        # Insights
        self.insight_list.clear()
        for insight in self.current_model.insights:
            colors = {"info": "#6aaae0", "warning": "#e0c06a", "critical": "#e06a6a"}
            color = colors.get(insight.severity, "#a0a0b0")
            item = QListWidgetItem(insight.title)
            item.setForeground(QColor(color))
            item.setToolTip(insight.description)
            self.insight_list.addItem(item)

        if not self.current_model.insights:
            item = QListWidgetItem("No insights yet")
            item.setForeground(QColor("#666"))
            self.insight_list.addItem(item)

        # Entries
        self.entry_list.clear()
        for entry in self.current_model.entries[:20]:
            icon = {
                KnowledgeType.FACT: "\U0001f4cc",
                KnowledgeType.PATTERN: "\U0001f50d",
                KnowledgeType.RECOMMENDATION: "\U0001f4a1",
                KnowledgeType.INSIGHT: "\U0001f9e0",
                KnowledgeType.LESSON: "\U0001f4d6",
                KnowledgeType.TIP: "\U0001f4a1",
            }.get(entry.type, "\U0001f4c4")
            text = "{} {}".format(icon, entry.title[:50])
            item = QListWidgetItem(text)
            item.setToolTip(entry.content[:200])
            self.entry_list.addItem(item)

        if not self.current_model.entries:
            item = QListWidgetItem("No knowledge yet")
            item.setForeground(QColor("#666"))
            self.entry_list.addItem(item)

    def _render_results(self, results):
        self.entry_list.clear()
        for entry in results:
            item = QListWidgetItem("\U0001f50d {}".format(entry.title[:50]))
            item.setToolTip(entry.content[:200])
            self.entry_list.addItem(item)
