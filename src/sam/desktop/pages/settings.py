from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QComboBox, QCheckBox,
    QGroupBox, QFormLayout
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from ...experience.models.settings import SettingsModel, SettingsItem, SettingsCategory
from ...operations.engine.settings import SettingsEngine


class SettingsPage(QWidget):
    """Halaman Settings untuk Desktop."""

    def __init__(self):
        super().__init__()
        self.settings_engine = SettingsEngine()
        self.current_model = None
        self._init_ui()
        self._start_refresh()

    def _init_ui(self):
        layout = QVBoxLayout()
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header
        header = QHBoxLayout()
        title = QLabel("\u2699\ufe0f Settings")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #e0e0e0;")
        header.addWidget(title)
        header.addStretch()

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

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        self.content = QWidget()
        self.content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(self.content)
        self.content_layout.setSpacing(16)

        scroll.setWidget(self.content)
        layout.addWidget(scroll)

        self.setLayout(layout)

    def _start_refresh(self):
        self.refresh()

    def refresh(self):
        try:
            model = self.settings_engine.get_settings()
            self.current_model = model
            self._render(model)
        except Exception as e:
            self._render_error(str(e))

    def _render(self, model):
        # Bersihkan layout
        self._clear_layout(self.content_layout)

        for section in model.sections:
            # Group box per kategori
            group = QGroupBox(section.name)
            group.setStyleSheet("""
                QGroupBox {
                    border: 1px solid #2a2a3a;
                    border-radius: 8px;
                    margin-top: 12px;
                    padding-top: 12px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 12px;
                    padding: 0 8px;
                    color: #e0e0e0;
                }
            """)
            form = QFormLayout()
            form.setSpacing(8)
            form.setContentsMargins(16, 16, 16, 16)

            for item in section.items:
                # Label
                label = QLabel(item.key)
                label.setStyleSheet("color: #a0a0b0;")

                # Value widget
                val_str = str(item.value)
                if val_str in ["true", "false"]:
                    widget = QCheckBox()
                    widget.setChecked(val_str == "true")
                    if not item.editable:
                        widget.setEnabled(False)
                elif val_str in ["autonomous", "supervised", "manual"]:
                    widget = QComboBox()
                    widget.addItems(["autonomous", "supervised", "manual"])
                    widget.setCurrentText(val_str)
                    if not item.editable:
                        widget.setEnabled(False)
                else:
                    widget = QLineEdit(val_str)
                    widget.setStyleSheet("""
                        QLineEdit {
                            background: #12121a;
                            border: 1px solid #2a2a3a;
                            border-radius: 4px;
                            padding: 4px 8px;
                            color: #e0e0e0;
                        }
                    """)
                    if not item.editable:
                        widget.setEnabled(False)

                # Description sebagai tooltip
                if item.description:
                    widget.setToolTip(item.description)

                form.addRow(label, widget)

            group.setLayout(form)
            self.content_layout.addWidget(group)

        # Spacer
        self.content_layout.addStretch()

    def _clear_layout(self, layout):
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _render_error(self, error):
        self._clear_layout(self.content_layout)
        error_label = QLabel("\u26a0\ufe0f Error loading settings: {}".format(error))
        error_label.setStyleSheet("color: #e06a6a; font-size: 14px; padding: 16px;")
        self.content_layout.addWidget(error_label)
