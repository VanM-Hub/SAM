"""QtStatusBar — Status bar runtime for the SAM Desktop.

Consumes StatusBar Sprint 15 model to display connection state,
refresh mode, missions, approvals, notifications, and theme.
No business logic. No domain imports.
"""

from __future__ import annotations

from typing import Optional, Dict, Tuple, List, Callable

try:
    from PySide6.QtWidgets import QStatusBar, QLabel, QWidget, QHBoxLayout
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False

from ..renderer_adapter import WidgetAction, DesktopRendererAdapter


class QtStatusBar:
    """Status bar runtime for the SAM Desktop.

    Displays: connection, refresh, missions, approvals,
    notifications, theme. Reads from StatusBar model.
    """

    def __init__(self, qstatusbar: Optional[QStatusBar] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._qsb = qstatusbar
        self._labels: Dict[str, QLabel] = {}

        # Permanent widgets (right side)
        self._perm_widgets: Dict[str, QLabel] = {}

    def build(self) -> Optional[QStatusBar]:
        """Build status bar with sections. Returns QStatusBar or None."""
        if not self._qsb:
            return None

        sb = self._qsb
        sb.setMaximumHeight(24)

        # Connection indicator (permanent-right)
        conn = QLabel("   [[connected]]   ")
        conn.setStyleSheet("color: #00FF00; font-weight: bold;")
        sb.addPermanentWidget(conn)
        self._perm_widgets["connection"] = conn

        # Refresh indicator
        ref = QLabel("  [auto]  ")
        sb.addPermanentWidget(ref)
        self._perm_widgets["refresh"] = ref

        # Mission count
        missions = QLabel("  0 missions  ")
        sb.addPermanentWidget(missions)
        self._perm_widgets["missions"] = missions

        # Approval badge
        approvals = QLabel("  !0  ")
        approvals.setStyleSheet("color: #FFD700;")
        sb.addPermanentWidget(approvals)
        self._perm_widgets["approvals"] = approvals

        # Notification count
        notif = QLabel("  @0  ")
        notif.setStyleSheet("color: #888888;")
        sb.addPermanentWidget(notif)
        self._perm_widgets["notifications"] = notif

        # Theme indicator
        theme_lbl = QLabel("  [dark]  ")
        sb.addPermanentWidget(theme_lbl)
        self._perm_widgets["theme"] = theme_lbl

        # Default message
        sb.showMessage("Ready")

        return sb

    # ── Updates ───────────────────────────────────────────────────────

    def update_from_text(self, text: str) -> None:
        """Update status bar from pre-composed text.

        Text format: the StatusBar compact_line or summary.
        """
        if not text or not self._qsb:
            return
        self._qsb.showMessage(text)

    def update_from_action(self, action: WidgetAction) -> None:
        """Update status bar from a WidgetAction."""
        if action.widget_id != "status_bar":
            return
        if action.action in ("set_content", "update"):
            self.update_from_text(action.data)

    def set_connection(self, connected: bool) -> None:
        """Set connection indicator state."""
        lbl = self._perm_widgets.get("connection")
        if not lbl:
            return
        if connected:
            lbl.setText("  [[connected]]  ")
            lbl.setStyleSheet("color: #00FF00; font-weight: bold;")
        else:
            lbl.setText("  [[disconnected]]  ")
            lbl.setStyleSheet("color: #FF4444; font-weight: bold;")

    def set_refresh(self, mode: str) -> None:
        lbl = self._perm_widgets.get("refresh")
        if lbl:
            lbl.setText(f"  [{mode}]  ")

    def set_missions(self, active: int, total: int) -> None:
        lbl = self._perm_widgets.get("missions")
        if lbl:
            lbl.setText(f"  {active}/{total}  ")

    def set_approvals(self, count: int, critical: int = 0) -> None:
        lbl = self._perm_widgets.get("approvals")
        if not lbl:
            return
        if critical > 0:
            lbl.setText(f"  !{count}*  ")
            lbl.setStyleSheet("color: #FF4444; font-weight: bold;")
        else:
            lbl.setText(f"  !{count}  ")
            lbl.setStyleSheet("color: #FFD700;" if count > 0 else "color: #888888;")

    def set_notifications(self, count: int) -> None:
        lbl = self._perm_widgets.get("notifications")
        if lbl:
            lbl.setText(f"  @{count}  ")

    def set_theme(self, name: str) -> None:
        lbl = self._perm_widgets.get("theme")
        if lbl:
            lbl.setText(f"  [{name}]  ")

    def set_message(self, text: str) -> None:
        if self._qsb:
            self._qsb.showMessage(text)

    # ── Bulk update ────────────────────────────────────────────────────

    def apply_status_bar_model(self, status_bar_model) -> None:
        """Apply a StatusBar (Sprint 15) model to the Qt status bar."""
        if not status_bar_model:
            return
        # Extract fields using getattr (safely)
        screen = getattr(status_bar_model, 'screen', None)
        refresh = getattr(status_bar_model, 'refresh_mode', None)
        is_paused = getattr(status_bar_model, 'is_paused', False)
        connection = getattr(status_bar_model, 'connection', None)
        active_missions = getattr(status_bar_model, 'active_missions', 0)
        total_missions = getattr(status_bar_model, 'total_missions', 0)
        pending_approvals = getattr(status_bar_model, 'pending_approvals', 0)
        critical_approvals = getattr(status_bar_model, 'critical_approvals', 0)
        unread = getattr(status_bar_model, 'unread_count', 0)
        theme_name = getattr(status_bar_model, 'theme', None)
        uptime = getattr(status_bar_model, 'uptime', None)

        # Update all indicators
        self.set_connection(connection == "connected")
        self.set_refresh(refresh or "auto")
        self.set_missions(active_missions, total_missions)
        self.set_approvals(pending_approvals, critical_approvals)
        self.set_notifications(unread)
        self.set_theme(theme_name or "dark")

        # Message: screen + uptime
        msg_parts = []
        if screen:
            msg_parts.append(f"Screen: {screen}")
        if uptime:
            msg_parts.append(f"Uptime: {uptime}")
        if is_paused:
            msg_parts.append("[PAUSED]")
        self.set_message(" | ".join(msg_parts))

    # ── Access ────────────────────────────────────────────────────────

    @property
    def widget(self) -> Optional[QStatusBar]:
        return self._qsb
