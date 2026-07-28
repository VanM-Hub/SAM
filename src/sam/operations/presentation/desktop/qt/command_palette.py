"""CommandPalette — Command palette for the SAM Desktop.

Mirrors VSCode palette (Ctrl+Shift+P). Displays:
> Open Mission
> Refresh Dashboard
> Approve Mission
> Change Theme
> Open Timeline
> ...

Commands sourced from CommandRegistry (Sprint 14). No duplicate.
"""

from __future__ import annotations

from typing import Optional, List, Callable, Dict, Tuple

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QLineEdit, QListWidget,
        QListWidgetItem, QDialog, QApplication,
    )
    from PySide6.QtCore import Qt, Signal
    from PySide6.QtGui import QKeySequence, QShortcut
    HAS_QT = True
except ImportError:
    HAS_QT = False


class CommandPalette:
    """Command palette dialog (Ctrl+Shift+P).

    Commands from CommandRegistry (Sprint 14).
    No registration duplication. No business logic.
    """

    def __init__(self, parent_widget: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")

        self._parent = parent_widget
        self._dialog: Optional[QDialog] = None
        self._search: Optional[QLineEdit] = None
        self._list: Optional[QListWidget] = None

        # Commands
        self._commands: List[Tuple[str, str, str]] = []
        # (display, command_name, category)

        # Callback
        self._on_execute: Optional[Callable[[str], None]] = None

        # Keyboard shortcut
        self._shortcut: Optional[QShortcut] = None

    def build(self) -> QDialog:
        """Build the command palette dialog."""
        dialog = QDialog(self._parent)
        dialog.setWindowTitle("Command Palette")
        dialog.setMinimumWidth(500)
        dialog.setMinimumHeight(400)
        dialog.setModal(False)
        dialog.setWindowFlags(
            Qt.WindowType.Popup
            | Qt.WindowType.FramelessWindowHint
        )

        layout = QVBoxLayout()
        dialog.setLayout(layout)

        # Search input
        search = QLineEdit()
        search.setPlaceholderText("> Type a command...")
        search.textChanged.connect(self._on_search_changed)
        search.returnPressed.connect(self._on_execute_selected)
        layout.addWidget(search)
        self._search = search

        # Command list
        cmd_list = QListWidget()
        cmd_list.itemClicked.connect(self._on_item_clicked)
        cmd_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(cmd_list)
        self._list = cmd_list

        # Connect escape to close
        dialog.rejected.connect(self._on_dialog_closed)

        self._dialog = dialog
        return dialog

    def register_shortcut(self, parent_widget: QWidget) -> QShortcut:
        """Register Ctrl+Shift+P shortcut to toggle palette."""
        shortcut = QShortcut(QKeySequence("Ctrl+Shift+P"), parent_widget)
        shortcut.activated.connect(self.toggle)
        self._shortcut = shortcut
        return shortcut

    # ── Commands ──────────────────────────────────────────────────────

    def load_from_registry(self, commands: List[object]) -> None:
        """Load commands from CommandRegistry entries.

        Args:
            commands: List of CommandEntry from CommandRegistry (Sprint 14).
        """
        seen: set = set()
        self._commands = []

        for cmd in commands:
            name = getattr(cmd, 'name', '')
            help_text = getattr(cmd, 'help_text', '')
            category = getattr(cmd, 'category', 'general')

            if name and name not in seen:
                seen.add(name)
                display = f"> {name}"
                if help_text:
                    display += f"  — {help_text}"
                self._commands.append((display, name, category))

        # Sort by category then name
        self._commands.sort(key=lambda c: (c[2], c[1]))

        # Add default commands not in registry
        defaults = [
            ("Open Dashboard", "dashboard", "navigation"),
            ("Open Missions", "missions", "navigation"),
            ("Open Approvals", "approvals", "navigation"),
            ("Open Timeline", "timeline", "navigation"),
            ("Open Trust", "trust", "navigation"),
            ("Refresh Dashboard", "refresh", "operations"),
            ("Approve Mission", "approve", "operations"),
            ("Change Theme", "theme", "settings"),
            ("Toggle Dark Mode", "theme dark", "settings"),
            ("Toggle Light Mode", "theme light", "settings"),
            ("Open Command Palette", "palette", "system"),
            ("Quit Application", "quit", "system"),
        ]
        for display, name, cat in defaults:
            if name not in seen:
                self._commands.append((display, name, cat))
                seen.add(name)

        self._rebuild()

    # ── UI ────────────────────────────────────────────────────────────

    def toggle(self) -> None:
        """Toggle palette visibility."""
        if not self._dialog:
            return
        if self._dialog.isVisible():
            self._dialog.close()
        else:
            self.show()

    def show(self) -> None:
        if not self._dialog:
            return
        # Center on parent
        if self._parent:
            parent_geo = self._parent.geometry()
            x = parent_geo.x() + (parent_geo.width() - self._dialog.width()) // 2
            y = parent_geo.y() + 100
            self._dialog.move(x, y)

        self._rebuild()
        self._dialog.show()
        if self._search:
            self._search.setFocus()
            self._search.clear()

    def hide(self) -> None:
        if self._dialog:
            self._dialog.close()

    # ── Events ────────────────────────────────────────────────────────

    def on_execute(self, handler: Callable[[str], None]) -> None:
        """Register execute callback."""
        self._on_execute = handler

    def _on_execute_selected(self) -> None:
        """Execute the currently selected command."""
        if not self._list:
            return
        item = self._list.currentItem()
        if not item:
            # First item
            if self._list.count() > 0:
                item = self._list.item(0)
            else:
                return

        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd and self._on_execute:
            self._on_execute(cmd)
        self.hide()

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd and self._on_execute:
            self._on_execute(cmd)
        self.hide()

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        if cmd and self._on_execute:
            self._on_execute(cmd)
        self.hide()

    def _on_dialog_closed(self) -> None:
        pass

    # ── Internal ──────────────────────────────────────────────────────

    def _on_search_changed(self, text: str) -> None:
        self._rebuild(text)

    def _rebuild(self, filter_text: str = "") -> None:
        if not self._list:
            return
        self._list.clear()

        ft = filter_text.lower()

        for display, cmd_name, category in self._commands:
            if ft and ft not in display.lower() and ft not in cmd_name.lower():
                continue
            item = QListWidgetItem(display)
            item.setData(Qt.ItemDataRole.UserRole, cmd_name)
            self._list.addItem(item)

    # ── Properties ────────────────────────────────────────────────────

    @property
    def dialog(self) -> Optional[QDialog]:
        return self._dialog

    @property
    def is_open(self) -> bool:
        return self._dialog is not None and self._dialog.isVisible()

    @property
    def command_count(self) -> int:
        return len(self._commands)

    def summary(self) -> str:
        return f"CommandPalette: {len(self._commands)} commands, {'open' if self.is_open else 'closed'}"
