"""
Desktop Operations Console — PySide6 application.
"""

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QStackedWidget, QLabel
from PySide6.QtCore import Qt

from ..experience.builder import ExperienceBuilder
from ..telemetry.service import TelemetryService
from .pages.home import HomePage


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAM Operations Console")
        self.setGeometry(100, 100, 1200, 800)
        self.setStyleSheet("background: #0a0a0f; color: #e0e0e0;")

        # Setup services
        self.telemetry = TelemetryService()
        self.builder = ExperienceBuilder(self.telemetry)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Sidebar
        sidebar = QWidget()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("background: #12121a; border-right: 1px solid #2a2a3a;")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setSpacing(8)
        sidebar_layout.setContentsMargins(16, 24, 16, 24)

        # Logo
        logo = QLabel("\u2699\ufe0f SAM")
        logo.setStyleSheet("font-size: 24px; font-weight: bold; color: #fff; margin-bottom: 24px;")
        sidebar_layout.addWidget(logo)

        # Pages
        self.pages = QStackedWidget()
        self.home_page = HomePage(self.builder)
        self.pages.addWidget(self.home_page)

        # Navigation
        self.nav_buttons = []
        nav_items = [("\U0001f3e0 Home", 0)]

        for label, index in nav_items:
            btn = QPushButton(label)
            btn.setStyleSheet("""
                QPushButton {
                    text-align: left;
                    padding: 10px 14px;
                    border: none;
                    border-radius: 8px;
                    color: #a0a0b0;
                    background: transparent;
                    font-size: 14px;
                }
                QPushButton:hover {
                    background: #1e1e2e;
                    color: #fff;
                }
                QPushButton:checked {
                    background: #2a2a4a;
                    color: #fff;
                }
            """)
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, idx=index: self._switch_page(idx))
            sidebar_layout.addWidget(btn)
            self.nav_buttons.append(btn)

        # Select first
        self.nav_buttons[0].setChecked(True)
        sidebar_layout.addStretch()

        # Content
        main_layout.addWidget(sidebar)
        main_layout.addWidget(self.pages, 1)

    def _switch_page(self, index: int):
        """Pindah halaman."""
        self.pages.setCurrentIndex(index)
        for i, btn in enumerate(self.nav_buttons):
            btn.setChecked(i == index)


def run():
    app = QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
