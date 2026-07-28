"""QtDashboardView — Dashboard view for the SAM Desktop.

Renders DashboardComposer output and WidgetRenderer content
as Qt widgets. Only visualization — no business logic.
"""

from __future__ import annotations

from typing import Optional, Dict, Any

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QFrame, QScrollArea, QGridLayout, QGroupBox,
    )
    from PySide6.QtCore import Qt
    from PySide6.QtGui import QFont
    HAS_QT = True
except ImportError:
    HAS_QT = False

from ..theme import DesktopThemeAdapter, DesktopTheme
from ..renderer_adapter import WidgetAction, DesktopRendererAdapter


class QtDashboardView:
    """Dashboard view for the SAM Desktop.

    Consumes WidgetActions from DesktopRendererAdapter and renders
    them as Qt widgets. No direct DTO access — data arrives already
    composed by DashboardComposer and serialized as WidgetActions.
    """

    def __init__(self, parent_widget: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._parent = parent_widget
        self._container: Optional[QWidget] = None
        self._theme: Optional[DesktopTheme] = None

        # Widgets cache
        self._widgets: Dict[str, QWidget] = {}

    def build(self) -> QWidget:
        """Build the dashboard view container."""
        container = QWidget()
        layout = QVBoxLayout()
        container.setLayout(layout)

        # Dashboard header
        header = QLabel("<h2>Dashboard</h2>")
        header.setAlignment(Qt.AlignLeft)

        # Content grid (2x2)
        grid = QGridLayout()

        # Create placeholder cards
        self._add_card(grid, "missions", "Missions", "-- active / -- total", 0, 0)
        self._add_card(grid, "health", "Health", "Loading...", 0, 1)
        self._add_card(grid, "trust", "Trust", "Grade: --", 1, 0)
        self._add_card(grid, "summary", "Summary", "No data yet", 1, 1)

        layout.addWidget(header)
        layout.addLayout(grid)
        layout.addStretch()

        self._container = container
        if self._parent:
            self._parent.layout().addWidget(container)

        return container

    def _add_card(self, grid: QGridLayout, card_id: str,
                  title: str, text: str, row: int, col: int) -> QGroupBox:
        """Add a dashboard card (group box with label)."""
        card = QGroupBox(title)
        card.setMinimumSize(200, 100)
        card_layout = QVBoxLayout()
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setWordWrap(True)
        card_layout.addWidget(label)
        card.setLayout(card_layout)
        grid.addWidget(card, row, col)
        self._widgets[card_id] = card
        return card

    # ── Render ────────────────────────────────────────────────────────

    def apply_action(self, action: WidgetAction) -> None:
        """Apply a single WidgetAction to the dashboard.

        Action.data contains pre-composed text from RendererProtocol.
        No raw DTO access.
        """
        if action.action != "set_content":
            return
        if action.widget_id == "dashboard":
            self._update_dashboard(action.data)

    def apply_actions(self, actions) -> None:
        """Apply multiple WidgetActions."""
        for action in actions:
            self.apply_action(action)

    def _update_dashboard(self, content: str) -> None:
        """Update dashboard from serialized content.

        Content format: "Dashboard | Missions: X | Health: Y | Trust: Z | ..."
        """
        if not content:
            return
        parts = content.split(" | ")
        for part in parts:
            if part.startswith("Missions:"):
                val = part.replace("Missions:", "").strip()
                self._update_card("missions", f"Active: {val}")
            elif part.startswith("Health:"):
                val = part.replace("Health:", "").strip()
                self._update_card("health", val.capitalize())
            elif part.startswith("Trust:"):
                val = part.replace("Trust:", "").strip()
                self._update_card("trust", f"Grade: {val}")

    def _update_card(self, card_id: str, text: str) -> None:
        """Update text inside a card group box."""
        card = self._widgets.get(card_id)
        if not card:
            return
        label = card.layout().itemAt(0).widget()
        if isinstance(label, QLabel):
            label.setText(text)

    # ── Theme ─────────────────────────────────────────────────────────

    def apply_theme(self, desktop_theme: DesktopTheme) -> None:
        """Apply theme colors to dashboard."""
        self._theme = desktop_theme
        if not self._container:
            return
        colors = desktop_theme.colors
        self._container.setStyleSheet(
            f"background-color: {colors.background};"
            f"color: {colors.foreground};"
        )

    # ── Access ────────────────────────────────────────────────────────

    @property
    def widget(self) -> Optional[QWidget]:
        return self._container

    def clear(self) -> None:
        """Clear all dashboard content."""
        for card_id in self._widgets:
            self._update_card(card_id, "--")
