"""DashboardWidget — Main dashboard view for the SAM Desktop.

Displays: Mission summary, Approval summary, Notification summary,
Health, Trust, Recent activity. All data from DashboardComposer.
No new queries. QWidget visualization only.
"""

from __future__ import annotations

from typing import Optional, Dict, Any, List

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
        QLabel, QFrame, QGroupBox, QScrollArea, QListWidget,
        QListWidgetItem,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False


class _CardWidget(QFrame):
    """A labeled card for dashboard metrics."""

    def __init__(self, title: str, value: str = "--", subtitle: str = ""):
        if not HAS_QT:
            return
        super().__init__()
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setMinimumSize(180, 100)

        layout = QVBoxLayout()
        self.setLayout(layout)

        # Title
        title_lbl = QLabel(f"<b>{title}</b>")
        title_lbl.setAlignment(Qt.AlignLeft)
        layout.addWidget(title_lbl)

        # Value
        self._value_lbl = QLabel(value)
        self._value_lbl.setAlignment(Qt.AlignCenter)
        f = self._value_lbl.font()
        f.setPointSize(f.pointSize() + 4)
        f.setBold(True)
        self._value_lbl.setFont(f)
        layout.addWidget(self._value_lbl)

        # Subtitle
        if subtitle:
            sub_lbl = QLabel(subtitle)
            sub_lbl.setAlignment(Qt.AlignCenter)
            sub_lbl.setStyleSheet("color: #888888;")
            layout.addWidget(sub_lbl)

    def set_value(self, value: str) -> None:
        self._value_lbl.setText(value)

    def set_color(self, color: str) -> None:
        self._value_lbl.setStyleSheet(f"color: {color}; font-weight: bold;")


class DashboardWidget:
    """Main dashboard with 6 summary cards + recent activity.

    All data from DashboardComposer via bridge pipeline.
    No new queries. No business logic.
    """

    def __init__(self, parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._parent = parent
        self._container: Optional[QScrollArea] = None

        # Cards
        self._cards: Dict[str, _CardWidget] = {}

        # Recent activity list
        self._activity_list: Optional[QListWidget] = None

    def build(self) -> QWidget:
        """Build the dashboard widget."""
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Title
        title = QLabel("<h2>Dashboard</h2>")
        layout.addWidget(title)

        # 3x2 grid for summary cards
        grid = QGridLayout()

        # Row 1: Mission summary, Approval summary
        self._add_card(grid, "missions", "Missions", "0 active / 0 total", 0, 0)
        self._add_card(grid, "approvals", "Approvals", "0 pending", 0, 1)

        # Row 2: Notification summary, Health
        self._add_card(grid, "notifications", "Notifications", "0 unread", 1, 0)
        self._add_card(grid, "health", "Health", "Unknown", 1, 1)

        # Row 3: Trust, Recent Activity
        self._add_card(grid, "trust", "Trust Score", "Grade: --", 2, 0)
        self._add_card(grid, "recent_activity", "Recent Activity", "No activity", 2, 1)

        layout.addLayout(grid)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        layout.addWidget(sep)

        # Activity detail list
        activity_lbl = QLabel("<b>Activity Log</b>")
        layout.addWidget(activity_lbl)

        activity_list = QListWidget()
        activity_list.setMaximumHeight(200)
        layout.addWidget(activity_list)
        self._activity_list = activity_list

        layout.addStretch()

        scroll.setWidget(container)
        self._container = scroll
        return scroll

    def _add_card(self, grid: QGridLayout, card_id: str,
                  title: str, value: str, row: int, col: int) -> None:
        card = _CardWidget(title, value)
        grid.addWidget(card, row, col)
        self._cards[card_id] = card

    # ── Data from DashboardComposer ──────────────────────────────────

    def update_from_dashboard(self, data: Dict[str, Any]) -> None:
        """Update dashboard from a DashboardComposer dict.

        Keys expected (all optional):
            mission_count, mission_active
            approval_pending
            notification_unread
            health_status
            trust_grade
            recent_activities (list of str)
        """
        # Missions
        active = data.get("mission_active", data.get("active_missions"))
        total = data.get("mission_count", data.get("total_missions"))
        if active is not None and total is not None:
            self._cards["missions"].set_value(f"{active} / {total}")
        elif active is not None:
            self._cards["missions"].set_value(f"{active} active")

        # Approvals
        pending = data.get("approval_pending", data.get("pending_approvals"))
        if pending is not None:
            self._cards["approvals"].set_value(f"{pending} pending")
            if pending > 0:
                self._cards["approvals"].set_color("#FFAA00")

        # Notifications
        unread = data.get("notification_unread", data.get("unread_count"))
        if unread is not None:
            self._cards["notifications"].set_value(f"{unread} unread")
            if unread > 0:
                self._cards["notifications"].set_color("#FF8800")

        # Health
        health = data.get("health_status", data.get("health"))
        if health:
            self._cards["health"].set_value(str(health).capitalize())
            color_map = {"healthy": "#00AA00", "degraded": "#FFAA00",
                         "critical": "#FF4444", "unknown": "#888888"}
            color = color_map.get(str(health).lower(), "#888888")
            self._cards["health"].set_color(color)

        # Trust
        trust = data.get("trust_grade", data.get("trust"))
        if trust:
            grade = str(trust)
            self._cards["trust"].set_value(f"Grade: {grade}")
            grade_colors = {"A": "#00AA00", "B": "#44AA00",
                            "C": "#FFAA00", "D": "#FF8800", "E": "#FF4444"}
            gc = grade_colors.get(grade.upper(), "#888888")
            self._cards["trust"].set_color(gc)

        # Recent activities
        activities = data.get("recent_activities", data.get("activities", []))
        if activities and self._activity_list:
            self._activity_list.clear()
            for act in activities:
                text = str(act) if isinstance(act, str) else str(act.get("description", act))
                self._activity_list.addItem(text)

    def update_from_text(self, text: str) -> None:
        """Update from serialized dashboard text.

        Format: "Dashboard | Missions: X/Y | Health: Y | Trust: Z"
        """
        if not text:
            return
        parts = text.split(" | ")
        for part in parts:
            if part.startswith("Missions:"):
                val = part.replace("Missions:", "").strip()
                self._cards["missions"].set_value(val)
            elif part.startswith("Health:"):
                val = part.replace("Health:", "").strip()
                self._cards["health"].set_value(val.capitalize())
                color_map = {"healthy": "#00AA00", "degraded": "#FFAA00",
                             "critical": "#FF4444"}
                c = color_map.get(val.lower(), "#888888")
                self._cards["health"].set_color(c)
            elif part.startswith("Trust:"):
                val = part.replace("Trust:", "").strip()
                self._cards["trust"].set_value(val)

    def update_approvals(self, count: int, critical: int = 0) -> None:
        self._cards["approvals"].set_value(f"{count} pending")
        if count > 0:
            self._cards["approvals"].set_color("#FF4444" if critical > 0 else "#FFAA00")

    def update_notifications(self, count: int) -> None:
        self._cards["notifications"].set_value(f"{count} unread")
        if count > 0:
            self._cards["notifications"].set_color("#FF8800")

    def update_missions(self, active: int, total: int) -> None:
        self._cards["missions"].set_value(f"{active} / {total}")

    def update_health(self, status: str) -> None:
        self._cards["health"].set_value(status.capitalize())
        color_map = {"healthy": "#00AA00", "degraded": "#FFAA00",
                     "critical": "#FF4444", "unknown": "#888888"}
        c = color_map.get(status.lower(), "#888888")
        self._cards["health"].set_color(c)

    def update_trust(self, grade: str) -> None:
        self._cards["trust"].set_value(f"Grade: {grade}")
        grade_colors = {"A": "#00AA00", "B": "#44AA00",
                        "C": "#FFAA00", "D": "#FF8800", "E": "#FF4444"}
        c = grade_colors.get(grade.upper(), "#888888")
        self._cards["trust"].set_color(c)

    def add_activity(self, description: str) -> None:
        if self._activity_list:
            self._activity_list.insertItem(0, description)
            # Keep max 100
            while self._activity_list.count() > 100:
                self._activity_list.takeItem(self._activity_list.count() - 1)

    # ── Access ───────────────────────────────────────────────────────

    @property
    def widget(self) -> Optional[QWidget]:
        return self._container

    def clear(self) -> None:
        for card_id, card in self._cards.items():
            card.set_value("--")
        if self._activity_list:
            self._activity_list.clear()

    def summary(self) -> str:
        return f"DashboardWidget: {len(self._cards)} cards active"
