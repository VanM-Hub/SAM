"""QtSystemTray — System tray for the SAM Desktop.

QSystemTrayIcon with notification support, minimize to tray, restore.
No business logic. No domain imports.
"""

from __future__ import annotations

from typing import Optional, Callable, Dict, List

try:
    from PySide6.QtWidgets import QSystemTrayIcon, QMenu, QWidget
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QIcon, QAction
    HAS_QT = True
except ImportError:
    HAS_QT = False
    QSystemTrayIcon = object


class QtSystemTray:
    """System tray for the SAM Desktop.

    Supports: notify, badge, minimize to tray, restore.
    """

    def __init__(self, parent_widget: QWidget, icon_name: str = "SAM"):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._parent = parent_widget
        self._icon_name = icon_name
        self._tray: Optional[QSystemTrayIcon] = None
        self._menu: Optional[QMenu] = None
        self._on_show: Optional[Callable] = None
        self._on_quit: Optional[Callable] = None
        self._supports_notifications = QSystemTrayIcon.supportsMessages()

    def build(self) -> Optional[QSystemTrayIcon]:
        """Build the system tray icon and menu.

        Returns None if system tray is not supported.
        """
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return None

        try:
            icon = QIcon.fromTheme(self._icon_name)
            if icon.isNull():
                icon = QIcon()
        except Exception:
            icon = QIcon()

        tray = QSystemTrayIcon(icon, self._parent)
        tray.setToolTip("SAM Desktop")

        # Context menu
        menu = QMenu()
        show_action = QAction("Show SAM")
        show_action.triggered.connect(self._on_show_action)
        menu.addAction(show_action)

        menu.addSeparator()

        quit_action = QAction("Quit")
        quit_action.triggered.connect(self._on_quit_action)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.activated.connect(self._on_activated)

        tray.show()
        self._tray = tray
        self._menu = menu
        return tray

    def _on_activated(self, reason) -> None:
        """Handle tray icon activation."""
        from PySide6.QtWidgets import QSystemTrayIcon

        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            if self._on_show:
                self._on_show()

    def _on_show_action(self) -> None:
        if self._on_show:
            self._on_show()

    def _on_quit_action(self) -> None:
        if self._on_quit:
            self._on_quit()

    # ── Events ────────────────────────────────────────────────────────

    def on_show(self, handler: Callable) -> None:
        self._on_show = handler

    def on_quit(self, handler: Callable) -> None:
        self._on_quit = handler

    # ── Notifications ─────────────────────────────────────────────────

    def notify(self, title: str, message: str, icon: int = 0, duration_ms: int = 5000) -> None:
        """Show a system tray notification.

        Args:
            title: Notification title
            message: Notification body
            icon: 0=Info, 1=Warning, 2=Critical
            duration_ms: Display duration in milliseconds
        """
        if not self._tray or not self._supports_notifications:
            return

        from PySide6.QtWidgets import QSystemTrayIcon
        icon_map = {
            0: QSystemTrayIcon.MessageIcon.Information,
            1: QSystemTrayIcon.MessageIcon.Warning,
            2: QSystemTrayIcon.MessageIcon.Critical,
        }
        self._tray.showMessage(
            title, message,
            icon_map.get(icon, QSystemTrayIcon.MessageIcon.Information),
            duration_ms,
        )

    # ── Badge ─────────────────────────────────────────────────────────

    def set_badge(self, count: int) -> None:
        """Set notification badge count.

        Note: QSystemTrayIcon does not natively support badges on all
        platforms. This is best-effort via tooltip.
        """
        if not self._tray:
            return
        if count > 0:
            self._tray.setToolTip(f"SAM Desktop — {count} notifications")
        else:
            self._tray.setToolTip("SAM Desktop")

    # ── Visibility ────────────────────────────────────────────────────

    def hide_window(self) -> None:
        """Minimize the parent window to tray."""
        self._parent.hide()

    def show_window(self) -> None:
        """Restore the parent window from tray."""
        self._parent.show()
        self._parent.activateWindow()
        self._parent.raise_()

    # ── Properties ────────────────────────────────────────────────────

    @property
    def tray(self) -> Optional[QSystemTrayIcon]:
        return self._tray

    @property
    def is_available(self) -> bool:
        return QSystemTrayIcon.isSystemTrayAvailable()

    @property
    def supports_notifications(self) -> bool:
        return self._supports_notifications

    # ── Cleanup ───────────────────────────────────────────────────────

    def shutdown(self) -> None:
        """Remove tray icon and cleanup."""
        if self._tray:
            self._tray.hide()
            self._tray = None
