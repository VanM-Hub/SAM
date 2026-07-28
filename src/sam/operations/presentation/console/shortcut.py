"""Shortcut — Keyboard shortcut registry for the SAM Console.

Pure mapping: key -> command/action.
No UI. No renderer. Just data.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, Optional, Tuple


# ── Modifier flags ────────────────────────────────────────────────────

MOD_NONE = 0
MOD_CTRL = 1
MOD_ALT = 2
MOD_SHIFT = 4


@dataclass(frozen=True)
class ShortcutEntry:
    """A single keyboard shortcut definition (immutable)."""
    key: str
    modifiers: int = MOD_NONE
    action: str = ""
    command: str = ""
    description: str = ""
    category: str = "general"

    def match(self, key: str, modifiers: int) -> bool:
        """Check if a key press matches this shortcut."""
        return self.key == key and self.modifiers == modifiers

    @property
    def display(self) -> str:
        """Human-readable shortcut string."""
        parts: list = []
        if self.modifiers & MOD_CTRL:
            parts.append("Ctrl")
        if self.modifiers & MOD_ALT:
            parts.append("Alt")
        if self.modifiers & MOD_SHIFT:
            parts.append("Shift")
        parts.append(self.key.upper())
        return "+".join(parts)

    @property
    def is_special(self) -> bool:
        """Check if this is a function key or escape."""
        return self.key.startswith("F") or self.key == "ESC"


# ── Full shortcut registry ────────────────────────────────────────────

_SHORTCUT_LIST: list = [
    # Function keys
    ShortcutEntry("F1", MOD_NONE, "navigate",
                  "help", "Show help screen", "navigation"),
    ShortcutEntry("F2", MOD_NONE, "navigate",
                  "dashboard", "Go to Dashboard", "navigation"),
    ShortcutEntry("F3", MOD_NONE, "navigate",
                  "missions", "Go to Missions", "navigation"),
    ShortcutEntry("F4", MOD_NONE, "navigate",
                  "timeline", "Go to Timeline", "navigation"),
    ShortcutEntry("F5", MOD_NONE, "refresh",
                  "refresh", "Refresh current view", "utility"),
    ShortcutEntry("F6", MOD_NONE, "navigate",
                  "approvals", "Go to Approvals", "navigation"),
    ShortcutEntry("F7", MOD_NONE, "navigate",
                  "trust", "Go to Trust", "navigation"),
    ShortcutEntry("F8", MOD_NONE, "navigate",
                  "history", "Go to History", "navigation"),
    ShortcutEntry("F9", MOD_NONE, "navigate",
                  "settings", "Go to Settings", "navigation"),
    ShortcutEntry("F10", MOD_NONE, "navigate",
                  "status", "Show system status", "operations"),

    # Ctrl combinations
    ShortcutEntry("R", MOD_CTRL, "refresh",
                  "refresh --force", "Force reload all data", "utility"),
    ShortcutEntry("Q", MOD_CTRL, "shutdown",
                  "exit", "Quit the console", "utility"),
    ShortcutEntry("L", MOD_CTRL, "clear",
                  "", "Clear the screen", "utility"),
    ShortcutEntry("D", MOD_CTRL, "navigate",
                  "dashboard", "Quick jump to Dashboard", "navigation"),
    ShortcutEntry("C", MOD_CTRL, "copy",
                  "", "Copy selected text (platform)", "utility"),
    ShortcutEntry("N", MOD_CTRL, "navigate",
                  "notifications", "Show notifications", "operations"),

    # Escape / special
    ShortcutEntry("ESC", MOD_NONE, "navigate",
                  "back", "Go back one screen", "navigation"),
    ShortcutEntry("TAB", MOD_NONE, "complete",
                  "", "Autocomplete current command", "utility"),

    # Number shortcuts (via keyboard)
    ShortcutEntry("1", MOD_NONE, "navigate",
                  "dashboard", "Quick nav: Dashboard", "navigation"),
    ShortcutEntry("2", MOD_NONE, "navigate",
                  "missions", "Quick nav: Missions", "navigation"),
    ShortcutEntry("3", MOD_NONE, "navigate",
                  "approvals", "Quick nav: Approvals", "navigation"),
    ShortcutEntry("4", MOD_NONE, "navigate",
                  "timeline", "Quick nav: Timeline", "navigation"),
    ShortcutEntry("5", MOD_NONE, "navigate",
                  "trust", "Quick nav: Trust", "navigation"),
    ShortcutEntry("6", MOD_NONE, "navigate",
                  "history", "Quick nav: History", "navigation"),
    ShortcutEntry("7", MOD_NONE, "navigate",
                  "settings", "Quick nav: Settings", "navigation"),
    ShortcutEntry("8", MOD_NONE, "navigate",
                  "help", "Quick nav: Help", "navigation"),
    ShortcutEntry("9", MOD_NONE, "navigate",
                  "status", "Quick nav: System Status", "navigation"),

    # Single char shortcuts
    ShortcutEntry("?", MOD_NONE, "help",
                  "help", "Show help information", "utility"),
    ShortcutEntry("R", MOD_NONE, "refresh",
                  "refresh", "Refresh current view", "utility"),
    ShortcutEntry("Q", MOD_NONE, "shutdown",
                  "exit", "Quit the console", "utility"),
    ShortcutEntry("H", MOD_NONE, "navigate",
                  "back", "Go back one screen", "navigation"),
]

SHORTCUTS: Tuple[ShortcutEntry, ...] = tuple(_SHORTCUT_LIST)


def _build_lookup() -> Tuple[Dict[str, ShortcutEntry], Dict[str, ShortcutEntry]]:
    """Build lookup dicts by key and by command."""
    by_key: dict = {}
    by_command: dict = {}
    for s in _SHORTCUT_LIST:
        compound = f"{s.modifiers}:{s.key}"
        by_key[compound] = s
        if s.command and s.command not in by_command:
            by_command[s.command] = s
    return by_key, by_command


_SHORTCUT_BY_KEY, _SHORTCUT_BY_COMMAND = _build_lookup()


class ShortcutRegistry:
    """Immutable registry of keyboard shortcuts.

    Usage:
        reg = ShortcutRegistry()
        entry = reg.match("F5", MOD_NONE)
        if entry:
            dispatcher.dispatch(entry.command)
    """

    @property
    def all(self) -> Tuple[ShortcutEntry, ...]:
        return SHORTCUTS

    def match(self, key: str, modifiers: int = 0) -> Optional[ShortcutEntry]:
        """Find a shortcut by key and modifiers.

        Args:
            key: Key pressed (e.g., "F1", "R", "ESC", "1").
            modifiers: Modifier flags (MOD_CTRL, MOD_ALT, MOD_SHIFT).

        Returns ShortcutEntry or None.
        """
        compound = f"{modifiers}:{key}"
        return _SHORTCUT_BY_KEY.get(compound)

    def by_command(self, command: str) -> Optional[ShortcutEntry]:
        """Find the first shortcut that maps to a given command."""
        return _SHORTCUT_BY_COMMAND.get(command)

    def by_category(self, category: str) -> Tuple[ShortcutEntry, ...]:
        """Get all shortcuts in a category."""
        return tuple(s for s in SHORTCUTS if s.category == category)

    def get_action(self, key: str, modifiers: int = 0) -> Optional[str]:
        """Get the action string for a key combo."""
        entry = self.match(key, modifiers)
        return entry.action if entry else None

    def get_command(self, key: str, modifiers: int = 0) -> Optional[str]:
        """Get the command string for a key combo."""
        entry = self.match(key, modifiers)
        return entry.command if entry else None

    def validate_all(self) -> bool:
        """Validate that all shortcuts have required fields.

        Returns True if all shortcuts are valid.
        """
        for s in SHORTCUTS:
            if not s.key or not s.action:
                return False
        return True

    def format_help(self, category: str = "") -> str:
        """Format shortcuts as a help string.

        If category is provided, only show shortcuts in that category.
        """
        shortcuts = (
            self.by_category(category) if category
            else SHORTCUTS
        )
        lines = []
        for s in shortcuts:
            lines.append(f"  {s.display:<16s} — {s.description}")
        return "\n".join(lines)
