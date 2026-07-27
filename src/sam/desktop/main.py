"""
Desktop Operations Console — PySide6 Application.

SATU produk. Satu konteks. Satu identitas.
Setiap halaman menerima ExperienceContext yang sama.
Tidak ada halaman yang query Runtime secara independen.
"""

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QStackedWidget, QLabel, QFrame, QSizePolicy,
    QSystemTrayIcon, QMenu,
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QFont, QIcon, QPalette, QColor, QAction

try:
    from ...experience.engine import ExperienceEngine
    from ...telemetry.service import TelemetryService
    from .context import ExperienceContextBuilder, ExperienceContext
    from .widgets import (
        StatusCard, AttentionBanner, RecommendationCard,
        TimelineWidget, SearchBar,
    )
    from .pages.home import HomePage
    from .pages.activity import ActivityPage
    from .pages.work import WorkPage
    from .pages.knowledge import KnowledgePage, HistoryPage, SettingsPage
    from .pages.assistant import NotificationPage, AssistantPage
except ValueError:
    import sys, os
    src = os.path.join(os.path.dirname(__file__), "..", "..")
    if src not in sys.path:
        sys.path.insert(0, os.path.abspath(src))
    from sam.experience.engine import ExperienceEngine
    from sam.telemetry.service import TelemetryService
    from sam.desktop.context import ExperienceContextBuilder, ExperienceContext
    from sam.desktop.widgets import (
        StatusCard, AttentionBanner, RecommendationCard,
        TimelineWidget, SearchBar,
    )
    from sam.desktop.pages.home import HomePage
    from sam.desktop.pages.activity import ActivityPage
    from sam.desktop.pages.work import WorkPage
    from sam.desktop.pages.knowledge import KnowledgePage, HistoryPage, SettingsPage
    from sam.desktop.pages.assistant import NotificationPage, AssistantPage

VERSION = "3.2.1"


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

BOTTOM_NAV = [
    # ("❓", "Help"),
    ("\U00002139", "About"),
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
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 10px 14px;
    color: #808090;
    font-size: 13px;
}
QPushButton:hover {
    background: #141422;
    color: #c0c0d0;
}
QPushButton:checked {
    background: #1a1a2a;
    color: #ffffff;
}
"""

BOTTOM_BUTTON_STYLE = """
QPushButton {
    text-align: left;
    background: transparent;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    color: #505060;
    font-size: 11px;
}
QPushButton:hover {
    background: #141422;
    color: #808090;
}
"""


class NavButton(QPushButton):
    def __init__(self, icon, text, index):
        super().__init__("  {}  {}".format(icon, text))
        self._nav_index = index
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setStyleSheet(NAV_BUTTON_STYLE)


class Sidebar(QWidget):
    """Persistent left navigation.
    Menu: Home, Activity, Work, Knowledge, History, Settings, Alerts, Ask
    Bottom: Help, About, Exit
    """

    def __init__(self, parent=None, exit_callback=None):
        super().__init__()
        self.setObjectName("sidebar")
        self.setStyleSheet(SIDEBAR_STYLE)
        self.setFixedWidth(180)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 16, 8, 16)
        layout.setSpacing(2)

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
            btn.clicked.connect(lambda *a, idx=index: parent.switch_page(idx))
            layout.addWidget(btn)
            self.buttons.append(btn)

        layout.addStretch()

        # Bottom — About
        about_btn = QPushButton("  \U00002139  About")
        about_btn.setStyleSheet(BOTTOM_BUTTON_STYLE)
        about_btn.setCursor(Qt.PointingHandCursor)
        about_btn.clicked.connect(self._show_about)
        layout.addWidget(about_btn)

        # Version
        version = QLabel("v{}".format(VERSION))
        version.setStyleSheet("color: #404050; font-size: 11px; padding: 8px 12px;")
        version.setAlignment(Qt.AlignCenter)
        layout.addWidget(version)

        self.setLayout(layout)
        self._parent = parent

    def _show_about(self):
        """Tampilkan About dialog (sederhana)."""
        from PySide6.QtWidgets import QMessageBox
        QMessageBox.about(
            self._parent,
            "About SAM",
            "SAM Operations Console v{}\n\n"
            "Single product operational experience.\n"
            "Runtime · Protection · Narrative".format(VERSION),
        )

    def select(self, index):
        for i, btn in enumerate(self.buttons):
            btn.setChecked(i == index)


# ============================================================================
# GlobalHeader — Sama di semua halaman
# ============================================================================

class GlobalHeader(QFrame):
    """Header yang sama untuk setiap halaman.
    Tidak pernah berubah antar halaman — hanya nilainya yang berubah.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setStyleSheet("""
            QFrame {
                background: #0d0d16;
                border-bottom: 1px solid #1a1a2a;
                padding: 0;
            }
        """)
        self.setFixedHeight(64)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(20, 0, 20, 0)
        layout.setSpacing(24)

        # Mission
        mission_w = QWidget()
        m_layout = QVBoxLayout(mission_w)
        m_layout.setContentsMargins(0, 8, 0, 8)
        m_layout.setSpacing(0)
        m_title = QLabel("MISSION")
        m_title.setStyleSheet("color: #505060; font-size: 9px; letter-spacing: 1px;")
        m_layout.addWidget(m_title)
        self._mission = QLabel("Protect OpenClaw Runtime")
        self._mission.setStyleSheet("color: #e0e0e0; font-size: 13px; font-weight: 500;")
        m_layout.addWidget(self._mission)
        layout.addWidget(mission_w)

        layout.addStretch()

        # Status badge
        self._status_badge = QFrame()
        s_layout = QHBoxLayout(self._status_badge)
        s_layout.setContentsMargins(8, 0, 8, 0)
        s_layout.setSpacing(6)
        self._status_dot = QLabel()
        self._status_dot.setFixedSize(8, 8)
        s_layout.addWidget(self._status_dot)
        self._status_text = QLabel("Healthy")
        self._status_text.setStyleSheet("color: #a0a0b0; font-size: 12px;")
        s_layout.addWidget(self._status_text)
        layout.addWidget(self._status_badge)

        # Attention
        self._attention_w = QWidget()
        a_layout = QHBoxLayout(self._attention_w)
        a_layout.setContentsMargins(0, 0, 0, 0)
        a_layout.setSpacing(4)
        self._attention_icon = QLabel()
        a_layout.addWidget(self._attention_icon)
        self._attention_text = QLabel()
        self._attention_text.setStyleSheet("color: #e0c06a; font-size: 12px;")
        a_layout.addWidget(self._attention_text)
        layout.addWidget(self._attention_w)
        self._attention_w.hide()

        # Last activity
        self._activity_w = QWidget()
        act_layout = QHBoxLayout(self._activity_w)
        act_layout.setContentsMargins(0, 0, 0, 0)
        act_layout.setSpacing(4)
        act_layout.addWidget(QLabel("\U0001f552"))
        self._activity_text = QLabel()
        self._activity_text.setStyleSheet("color: #606070; font-size: 11px;")
        act_layout.addWidget(self._activity_text)
        layout.addWidget(self._activity_w)

        # Notification icon
        self._notif_btn = QPushButton()
        self._notif_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
                padding: 6px 10px;
                color: #808090;
                font-size: 13px;
            }
            QPushButton:hover { background: #1a1a2a; }
        """)
        self._notif_btn.setCursor(Qt.PointingHandCursor)
        layout.addWidget(self._notif_btn)

    def update_from_context(self, ctx: ExperienceContext):
        """Update dari ExperienceContext — bukan dari Runtime."""
        # Mission
        self._mission.setText(ctx.mission_name)

        # Status
        color = ctx.status_color
        self._status_dot.setStyleSheet(
            "background: {}; border-radius: 4px;".format(color)
        )
        self._status_text.setText(ctx.status_label)

        # Attention
        if ctx.needs_attention:
            self._attention_icon.setText("\u26a0\ufe0f")
            self._attention_text.setText("{} Action Required".format(ctx.attention_count))
            self._attention_w.show()
        else:
            self._attention_w.hide()

        # Last activity
        if ctx.last_activity_description:
            self._activity_text.setText("{} — {}".format(
                ctx.last_activity_time,
                ctx.last_activity_description[:30],
            ))
            self._activity_w.show()
        else:
            self._activity_w.hide()

        # Notification
        if ctx.unread_count > 0:
            self._notif_btn.setText("\U0001f514  {}".format(ctx.unread_count))
            self._notif_btn.setStyleSheet("""
                QPushButton {
                    background: #1a1a2a;
                    border: 1px solid #2a2a4a;
                    border-radius: 4px;
                    padding: 6px 10px;
                    color: #c0c0d0;
                    font-size: 12px;
                }
                QPushButton:hover { background: #2a2a3a; }
            """)
        else:
            self._notif_btn.setText("\U0001f514")
            self._notif_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 10px;
                    color: #606070;
                    font-size: 13px;
                }
                QPushButton:hover { background: #1a1a2a; }
            """)


# ============================================================================
# Main Window
# ============================================================================

class OperationsConsole(QMainWindow):
    """SAM Operations Console — satu produk."""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("SAM Operations Console")
        self.setMinimumSize(900, 600)
        self.resize(1100, 680)
        self.setStyleSheet("""
            QMainWindow { background: #0a0a10; }
            QWidget { color: #e0e0e0; }
        """)

        # Services
        self.telemetry = TelemetryService()
        self.experience = ExperienceEngine(self.telemetry)
        self._ctx_builder = ExperienceContextBuilder(self.experience)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Sidebar
        self.sidebar = Sidebar(self, exit_callback=self.close)
        main_layout.addWidget(self.sidebar)

        # Content area
        content_frame = QWidget()
        content_frame.setStyleSheet("background: #0a0a10;")
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        # Global Header
        self.header = GlobalHeader()
        content_layout.addWidget(self.header)

        # Attention banner
        self.attention_banner = AttentionBanner()
        self.attention_banner.action_clicked.connect(lambda a: self.switch_page(9) if a == "view" else None)
        content_layout.addWidget(self.attention_banner)
        self.attention_banner.hide()

        # Pages
        self.pages = QStackedWidget()
        self.pages.setStyleSheet("background: transparent;")

        self.home_page = HomePage(self.experience, self._ctx_builder)
        self.activity_page = ActivityPage(self.experience, self._ctx_builder)
        self.work_page = WorkPage(self.experience, self._ctx_builder)
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

        content_layout.addWidget(self.pages, 1)
        main_layout.addWidget(content_frame, 1)

        # Context refresh
        self._refresh_timer = QTimer()
        self._refresh_timer.timeout.connect(self._refresh_context)
        self._refresh_timer.start(3000)

        # Keyboard shortcuts
        self._setup_shortcuts()

        # Initial
        self.switch_page(0)

    def _setup_shortcuts(self):
        """Keyboard navigation."""
        from PySide6.QtGui import QShortcut, QKeySequence

        # Ctrl+K — search
        self._search_shortcut = QShortcut(QKeySequence("Ctrl+K"), self)
        self._search_shortcut.activated.connect(self._focus_search)

        # Ctrl+R — refresh
        self._refresh_shortcut = QShortcut(QKeySequence("Ctrl+R"), self)
        self._refresh_shortcut.activated.connect(self._force_refresh)

        # Escape — close dialogs / go home
        self._esc_shortcut = QShortcut(QKeySequence("Escape"), self)
        self._esc_shortcut.activated.connect(lambda: self.switch_page(0))

        # Number shortcuts
        for i in range(1, 9):
            sc = QShortcut(QKeySequence("Ctrl+{}".format(i)), self)
            sc.activated.connect(lambda idx=i-1: self.switch_page(idx))

    def _focus_search(self):
        """Focus search di page aktif."""
        page = self.pages.currentWidget()
        if hasattr(page, 'search_input'):
            page.search_input.setFocus()

    def _force_refresh(self):
        """Refresh semua."""
        self._refresh_context()
        page = self.pages.currentWidget()
        if hasattr(page, 'refresh'):
            page.refresh()

    def _refresh_context(self):
        """Update konteks global — semua widget yang subscribe otomatis update."""
        try:
            ctx = self._ctx_builder.build()
            self.header.update_from_context(ctx)
            self.attention_banner.update_from_context(ctx)

            # Kirim ctx ke page aktif jika mendukung
            page = self.pages.currentWidget()
            if hasattr(page, 'update_context'):
                page.update_context(ctx)
        except Exception:
            pass

    def switch_page(self, index):
        """Ganti halaman — hanya konten yang berubah."""
        if 0 <= index < self.pages.count():
            self.pages.setCurrentIndex(index)
            self.sidebar.select(index)
            self._refresh_context()


# ============================================================================
# Entry Point
# ============================================================================

def run():
    import sys as _sys
    app = QApplication.instance() or QApplication(_sys.argv)
    app.setApplicationName("SAM Operations Console")
    app.setApplicationVersion(VERSION)

    # Dark palette
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor("#0a0a10"))
    palette.setColor(QPalette.WindowText, QColor("#e0e0e0"))
    palette.setColor(QPalette.Base, QColor("#12121a"))
    palette.setColor(QPalette.Text, QColor("#e0e0e0"))
    palette.setColor(QPalette.Button, QColor("#1a1a2a"))
    palette.setColor(QPalette.ButtonText, QColor("#e0e0e0"))
    palette.setColor(QPalette.Highlight, QColor("#2a4a6a"))
    palette.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    window = OperationsConsole()
    window.show()
    _sys.exit(app.exec())
