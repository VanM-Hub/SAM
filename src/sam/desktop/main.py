"""
Desktop Operations Console — PySide6 Application.

UI hanya membaca Experience Engine, bukan Runtime atau Telemetry langsung.
"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame, QSizePolicy,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QPalette, QColor

try:
    # Ketika dipanggil sebagai module
    from ...experience.engine import ExperienceEngine
    from ...telemetry.service import TelemetryService
    from .pages.home import HomePage
    from .pages.activity import ActivityPage
    from .pages.work import WorkPage
    from .pages.knowledge import KnowledgePage, HistoryPage, SettingsPage
    from .pages.assistant import NotificationPage, AssistantPage
except ValueError:
    # Ketika dipanggil langsung
    import sys, os
    src = os.path.join(os.path.dirname(__file__), "..", "..")
    if src not in sys.path:
        sys.path.insert(0, os.path.abspath(src))
    from sam.experience.engine import ExperienceEngine
    from sam.telemetry.service import TelemetryService
    from sam.desktop.pages.home import HomePage
    from sam.desktop.pages.activity import ActivityPage
    from sam.desktop.pages.work import WorkPage
    from sam.desktop.pages.knowledge import KnowledgePage, HistoryPage, SettingsPage
    from sam.desktop.pages.assistant import NotificationPage, AssistantPage


# ============================================================================
# Navigation
# ============================================================================

NAV_ITEMS = [
    ("\U0001f3e0", "Home", 0),
    ("\U0001f4cb", "Activity", 1),
    ("\u2705", "Work", 2),
    ("\U0001f4a1", "Knowledge", 3),
    ("\U0001f4dc", "History", 4),
    ("\u2699\ufe0f", "Settings", 5),
    ("\U0001f514", "Alerts", 6),
    ("\U0001f9e0", "Ask", 7),
]

SIDEBAR_STYLE = """
QWidget#sidebar {
    background: #0d0d14;
    border-right: 1px solid #1a1a2a;
}
"""

NAV_BUTTON_STYLE = """
QPushButton {
    text-align: left;
    padding: 10px 16px;
    border: none;
    border-radius: 8px;
    color: #808090;
    background: transparent;
    font-size: 13px;
    font-weight: 500;
}
QPushButton:hover {
    background: #161622;
    color: #e0e0e0;
}
QPushButton:checked {
    background: #1a1a30;
    color: #ffffff;
}
QPushButton:pressed {
    background: #202040;
}
"""


class NavButton(QPushButton):
    def __init__(self, icon, text, page_index, parent=None):
        super().__init__(parent)
        self.page_index = page_index
        self.setText(" {}  {}".format(icon, text))
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(NAV_BUTTON_STYLE)
        self.setFixedHeight(42)


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setStyleSheet(SIDEBAR_STYLE)
        self.setFixedWidth(200)

        layout = QVBoxLayout()
        layout.setSpacing(2)
        layout.setContentsMargins(8, 16, 8, 16)

        # Logo
        logo = QLabel("  SAM")
        logo.setStyleSheet("""
            font-size: 22px;
            font-weight: bold;
            color: #ffffff;
            padding: 8px 12px;
            margin-bottom: 16px;
        """)
        layout.addWidget(logo)

        # Navigation buttons
        self.buttons = []
        for icon, text, index in NAV_ITEMS:
            btn = NavButton(icon, text, index)
            btn.clicked.connect(lambda ch, idx=index: parent.switch_page(idx))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

        # Version
        version = QLabel("v3.1.0")
        version.setStyleSheet("color: #404050; font-size: 11px; padding: 8px 12px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        self.setLayout(layout)

    def select(self, index):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)


class OperationsConsole(QMainWindow):
    """Main window — SAM Operations Console."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAM Operations Console")
        self.setMinimumSize(900, 600)
        self.resize(1100, 680)
        self.setStyleSheet("""
            QMainWindow {
                background: #0a0a10;
            }
            QWidget {
                color: #e0e0e0;
            }
        """)

        # Services
        self.telemetry = TelemetryService()
        self.experience = ExperienceEngine(self.telemetry)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self)
        main_layout.addWidget(self.sidebar)

        # Content
        content_container = QFrame()
        content_container.setStyleSheet("background: #0a0a10;")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)

        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background: transparent;")

        # Create pages — all read from Experience Engine
        self.home_page = HomePage(self.experience)
        self.activity_page = ActivityPage(self.experience)
        self.work_page = WorkPage(self.experience)
        self.knowledge_page = KnowledgePage(self.experience)
        self.history_page = HistoryPage(self.experience)
        self.settings_page = SettingsPage(self.experience)
        self.notification_page = NotificationPage(self.experience)
        self.assistant_page = AssistantPage(self.experience)

        self.pages.addWidget(self.home_page)          # 0
        self.pages.addWidget(self.activity_page)      # 1
        self.pages.addWidget(self.work_page)          # 2
        self.pages.addWidget(self.knowledge_page)     # 3
        self.pages.addWidget(self.history_page)       # 4
        self.pages.addWidget(self.settings_page)      # 5
        self.pages.addWidget(self.notification_page)  # 6
        self.pages.addWidget(self.assistant_page)     # 7

        content_layout.addWidget(self.pages)
        main_layout.addWidget(content_container, 1)

        # Start on Home
        self.switch_page(0)

        # Refresh timer
        self.refresh_timer = QTimer()
        self.refresh_timer.timeout.connect(self.refresh_all)
        self.refresh_timer.start(5000)

    def switch_page(self, index):
        """Pindah halaman."""
        self.pages.setCurrentIndex(index)
        self.sidebar.select(index)
        # Trigger refresh for the selected page
        widget = self.pages.widget(index)
        if hasattr(widget, 'refresh'):
            widget.refresh()

    def refresh_all(self):
        """Refresh semua halaman (dipanggil tiap 5 detik)."""
        current = self.pages.currentIndex()
        widget = self.pages.widget(current)
        if hasattr(widget, 'refresh'):
            widget.refresh()


def run():
    app = QApplication([])
    window = OperationsConsole()
    window.show()
    app.exec()
