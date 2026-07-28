"""OperatorProductivity — Productivity tools for SAM Desktop operator.

Features: recent commands, favorite commands, pinned mission,
quick jump, bookmark timeline, clipboard helper, search everywhere.

No business logic. No domain access. All data from DTO or local state.
"""

from __future__ import annotations

from typing import Optional, List, Dict, Callable, Set
from collections import deque
from dataclasses import dataclass, field
import json
import os

try:
    from PySide6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel,
        QPushButton, QLineEdit, QListWidget, QListWidgetItem,
        QGroupBox, QFrame, QMenu, QApplication,
        QMessageBox, QDialog, QDialogButtonBox,
        QCompleter, QScrollArea, QSplitter, QCheckBox,
    )
    from PySide6.QtCore import Qt, QTimer, QStringListModel, Signal
    from PySide6.QtGui import QKeySequence, QShortcut, QColor, QBrush
    HAS_QT = True
except ImportError:
    HAS_QT = False


# ── Data models ──────────────────────────────────────────────────────

@dataclass
class RecentCommand:
    """A recently executed command."""
    command: str
    timestamp: str = ""
    category: str = ""

    def to_dict(self) -> dict:
        return {"command": self.command, "timestamp": self.timestamp,
                "category": self.category}


@dataclass
class FavoriteCommand:
    """A user-favorited command."""
    command: str
    label: str = ""
    shortcut: str = ""

    def to_dict(self) -> dict:
        return {"command": self.command, "label": self.label,
                "shortcut": self.shortcut}


@dataclass
class Bookmark:
    """A timeline event bookmark."""
    label: str
    event_description: str = ""
    event_time: str = ""
    mission_id: str = ""

    def to_dict(self) -> dict:
        return {"label": self.label, "event_description": self.event_description,
                "event_time": self.event_time, "mission_id": self.mission_id}


# ── Productivity Manager ─────────────────────────────────────────────

class ProductivityManager:
    """Manages operator productivity state.

    All state is local to the desktop session.
    No domain access. No business logic.
    """

    def __init__(self, max_recent: int = 50):
        self._recent_commands: deque = deque(maxlen=max_recent)
        self._favorite_commands: Dict[str, FavoriteCommand] = {}
        self._pinned_missions: Set[str] = set()
        self._bookmarks: List[Bookmark] = []
        self._last_search: str = ""

    # ── Recent Commands ──────────────────────────────────────────────

    def add_recent_command(self, command: str, category: str = "") -> None:
        cmd = RecentCommand(command=command, category=category)
        # Remove duplicates before add
        self._recent_commands = deque(
            [c for c in self._recent_commands if c.command != command],
            maxlen=self._recent_commands.maxlen,
        )
        self._recent_commands.append(cmd)

    @property
    def recent_commands(self) -> List[RecentCommand]:
        return list(self._recent_commands)

    @property
    def recent_command_texts(self) -> List[str]:
        return [c.command for c in self._recent_commands]

    def clear_recent(self) -> None:
        self._recent_commands.clear()

    # ── Favorite Commands ────────────────────────────────────────────

    def add_favorite(self, command: str, label: str = "",
                     shortcut: str = "") -> None:
        self._favorite_commands[command] = FavoriteCommand(
            command=command, label=label or command, shortcut=shortcut)

    def remove_favorite(self, command: str) -> None:
        self._favorite_commands.pop(command, None)

    def is_favorite(self, command: str) -> bool:
        return command in self._favorite_commands

    def toggle_favorite(self, command: str, label: str = "",
                        shortcut: str = "") -> bool:
        """Toggle favorite status. Returns True if now favorited."""
        if command in self._favorite_commands:
            self.remove_favorite(command)
            return False
        self.add_favorite(command, label, shortcut)
        return True

    @property
    def favorite_commands(self) -> List[FavoriteCommand]:
        return list(self._favorite_commands.values())

    @property
    def favorite_command_texts(self) -> List[str]:
        return [f.command for f in self._favorite_commands.values()]

    # ── Pinned Missions ──────────────────────────────────────────────

    def pin_mission(self, mission_id: str) -> None:
        self._pinned_missions.add(mission_id)

    def unpin_mission(self, mission_id: str) -> None:
        self._pinned_missions.discard(mission_id)

    def toggle_pin(self, mission_id: str) -> bool:
        """Toggle pin status. Returns True if now pinned."""
        if mission_id in self._pinned_missions:
            self._pinned_missions.discard(mission_id)
            return False
        self._pinned_missions.add(mission_id)
        return True

    def is_pinned(self, mission_id: str) -> bool:
        return mission_id in self._pinned_missions

    @property
    def pinned_missions(self) -> List[str]:
        return sorted(self._pinned_missions)

    @property
    def pinned_count(self) -> int:
        return len(self._pinned_missions)

    # ── Bookmarks ────────────────────────────────────────────────────

    def add_bookmark(self, label: str, description: str = "",
                     time: str = "", mission: str = "") -> None:
        self._bookmarks.append(Bookmark(
            label=label, event_description=description,
            event_time=time, mission_id=mission,
        ))

    def remove_bookmark(self, index: int) -> None:
        if 0 <= index < len(self._bookmarks):
            self._bookmarks.pop(index)

    @property
    def bookmarks(self) -> List[Bookmark]:
        return list(self._bookmarks)

    def clear_bookmarks(self) -> None:
        self._bookmarks.clear()

    # ── Search ───────────────────────────────────────────────────────

    @property
    def last_search(self) -> str:
        return self._last_search

    def set_last_search(self, text: str) -> None:
        self._last_search = text

    # ── Persistence ──────────────────────────────────────────────────

    def to_dict(self) -> dict:
        return {
            "recent_commands": [c.to_dict() for c in self._recent_commands],
            "favorite_commands": [f.to_dict() for f in self._favorite_commands.values()],
            "pinned_missions": list(self._pinned_missions),
            "bookmarks": [b.to_dict() for b in self._bookmarks],
        }

    def from_dict(self, data: dict) -> None:
        if not data:
            return
        self._recent_commands = deque(
            [RecentCommand(**c) for c in data.get("recent_commands", [])],
            maxlen=self._recent_commands.maxlen,
        )
        self._favorite_commands = {
            f["command"]: FavoriteCommand(**f)
            for f in data.get("favorite_commands", [])
        }
        self._pinned_missions = set(data.get("pinned_missions", []))
        self._bookmarks = [Bookmark(**b) for b in data.get("bookmarks", [])]

    def summary(self) -> str:
        return (
            f"ProductivityManager: {len(self._recent_commands)} recent, "
            f"{len(self._favorite_commands)} favorites, "
            f"{self.pinned_count} pinned, "
            f"{len(self._bookmarks)} bookmarks"
        )


# ── Productivity Panel Widget ────────────────────────────────────────

class ProductivityPanel(QWidget):
    """Productivity panel for quick access to productivity tools."""

    command_selected = Signal(str)  # emitted when operator selects a command

    def __init__(self, manager: Optional[ProductivityManager] = None,
                 parent: Optional[QWidget] = None):
        if not HAS_QT:
            raise ImportError("PySide6 is required")
        super().__init__(parent)

        self._manager = manager or ProductivityManager()
        self._build()

    def _build(self) -> None:
        layout = QVBoxLayout()
        self.setLayout(layout)

        # ── Quick Search ────────────────────────────────────────────
        search_group = QGroupBox("Quick Search")
        search_layout = QVBoxLayout()
        search_group.setLayout(search_layout)

        self._search_input = QLineEdit()
        self._search_input.setPlaceholderText("Search commands, missions, events...")
        self._search_input.setClearButtonEnabled(True)
        self._search_input.returnPressed.connect(self._on_search)
        self._search_input.setStyleSheet("padding: 6px; font-size: 14px;")
        search_layout.addWidget(self._search_input)

        self._search_results = QListWidget()
        self._search_results.setMaximumHeight(200)
        self._search_results.itemClicked.connect(self._on_result_clicked)
        self._search_results.setVisible(False)
        search_layout.addWidget(self._search_results)

        layout.addWidget(search_group)

        # ── Pinned Missions ─────────────────────────────────────────
        pinned_group = QGroupBox("Pinned Missions")
        pinned_layout = QVBoxLayout()
        pinned_group.setLayout(pinned_layout)

        self._pinned_list = QListWidget()
        self._pinned_list.setMaximumHeight(120)
        self._pinned_list.itemClicked.connect(self._on_pinned_clicked)
        pinned_layout.addWidget(self._pinned_list)

        layout.addWidget(pinned_group)

        # ── Recent Commands ─────────────────────────────────────────
        recent_group = QGroupBox("Recent Commands")
        recent_layout = QVBoxLayout()
        recent_group.setLayout(recent_layout)

        self._recent_list = QListWidget()
        self._recent_list.setMaximumHeight(150)
        self._recent_list.itemClicked.connect(self._on_recent_clicked)
        recent_layout.addWidget(self._recent_list)

        layout.addWidget(recent_group)

        # ── Favorites ───────────────────────────────────────────────
        fav_group = QGroupBox("Favorite Commands")
        fav_layout = QVBoxLayout()
        fav_group.setLayout(fav_layout)

        self._fav_list = QListWidget()
        self._fav_list.setMaximumHeight(120)
        self._fav_list.itemClicked.connect(self._on_fav_clicked)
        fav_layout.addWidget(self._fav_list)

        layout.addWidget(fav_group)

        # ── Context menu for lists ──────────────────────────────────
        self._recent_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._recent_list.customContextMenuRequested.connect(
            lambda pos: self._show_list_context_menu(self._recent_list, pos))

        self._fav_list.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self._fav_list.customContextMenuRequested.connect(
            lambda pos: self._show_list_context_menu(self._fav_list, pos))

    def refresh(self) -> None:
        """Refresh all lists from manager."""
        self._update_pinned()
        self._update_recent()
        self._update_favorites()

    def _update_pinned(self) -> None:
        self._pinned_list.clear()
        for mid in self._manager.pinned_missions:
            item = QListWidgetItem(f"📌 {mid}")
            item.setData(Qt.ItemDataRole.UserRole, mid)
            self._pinned_list.addItem(item)

    def _update_recent(self) -> None:
        self._recent_list.clear()
        for cmd in reversed(self._manager.recent_commands):
            item = QListWidgetItem(cmd.command)
            item.setData(Qt.ItemDataRole.UserRole, cmd.command)
            self._recent_list.addItem(item)

    def _update_favorites(self) -> None:
        self._fav_list.clear()
        for fav in self._manager.favorite_commands:
            label = fav.label or fav.command
            text = f"⭐ {label}"
            if fav.shortcut:
                text += f"  [{fav.shortcut}]"
            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, fav.command)
            self._fav_list.addItem(item)

    def _on_search(self) -> None:
        text = self._search_input.text().strip()
        if not text:
            self._search_results.setVisible(False)
            return

        self._manager.set_last_search(text)

        # Search through recent + favorites + pinned
        results = set()
        for cmd in self._manager.recent_command_texts:
            if text.lower() in cmd.lower():
                results.add(cmd)
        for cmd in self._manager.favorite_command_texts:
            if text.lower() in cmd.lower():
                results.add(cmd)
        for mid in self._manager.pinned_missions:
            if text.lower() in mid.lower():
                results.add(f"mission {mid}")

        if results:
            self._search_results.clear()
            for r in sorted(results):
                self._search_results.addItem(r)
            self._search_results.setVisible(True)
        else:
            # If no results, suggest from pinned missions
            self._search_results.setVisible(False)

    def _on_result_clicked(self, item: QListWidgetItem) -> None:
        text = item.text()
        self.command_selected.emit(text)
        self._search_results.setVisible(False)

    def _on_pinned_clicked(self, item: QListWidgetItem) -> None:
        mission_id = item.data(Qt.ItemDataRole.UserRole)
        self.command_selected.emit(f"inspect {mission_id}")

    def _on_recent_clicked(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        self.command_selected.emit(cmd)

    def _on_fav_clicked(self, item: QListWidgetItem) -> None:
        cmd = item.data(Qt.ItemDataRole.UserRole)
        self.command_selected.emit(cmd)

    def _show_list_context_menu(self, list_widget: QListWidget, pos) -> None:
        item = list_widget.itemAt(pos)
        if not item:
            return
        text = item.data(Qt.ItemDataRole.UserRole)

        menu = QMenu(self)
        fav = menu.addAction(
            "Remove from Favorites" if self._manager.is_favorite(text)
            else "Add to Favorites")
        menu.addSeparator()
        run = menu.addAction("Run Command")

        action = menu.exec_(list_widget.viewport().mapToGlobal(pos))
        if action == fav:
            self._manager.toggle_favorite(text)
            self.refresh()
        elif action == run:
            self.command_selected.emit(text)

    def set_manager(self, manager: ProductivityManager) -> None:
        self._manager = manager
        self.refresh()

    def summary(self) -> str:
        return f"ProductivityPanel: {self._manager.summary()}"
