"""CommandRegistry — Immutable command registry for the SAM Console.

All commands, aliases, help text, and autocomplete metadata in one place.
Used by the Console App for dispatching. Not a replacement for Sprint 13
CommandDispatcher — registry is the data source, dispatcher is the runtime.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, FrozenSet, List, Optional, Tuple


@dataclass(frozen=True)
class CommandEntry:
    """A single command definition (immutable)."""
    name: str
    help_text: str
    usage: str
    aliases: Tuple[str, ...] = ()
    category: str = "general"
    requires_mission: bool = False
    requires_approval: bool = False
    autocomplete_min_args: int = 0
    permission: str = "user"


# ── Full command registry ─────────────────────────────────────────────

_COMMAND_LIST: List[CommandEntry] = [
    # Navigation
    CommandEntry("dashboard", "Go to the operational dashboard.",
                 "dashboard", aliases=("dash", "home", "d"), category="navigation"),
    CommandEntry("missions", "View and manage active missions.",
                 "missions [filter]", aliases=("m", "mission"), category="navigation"),
    CommandEntry("approvals", "Review pending approval requests.",
                 "approvals", aliases=("a",), category="navigation"),
    CommandEntry("timeline", "Browse operational event history.",
                 "timeline [filter]", aliases=("t", "tl"), category="navigation"),
    CommandEntry("trust", "Monitor trust scores and decision quality.",
                 "trust", aliases=("ts",), category="navigation"),
    CommandEntry("history", "Review past missions and decisions.",
                 "history [limit]", aliases=("h",), category="navigation"),
    CommandEntry("settings", "Configure console and system preferences.",
                 "settings [key=value]", aliases=("set", "cfg"), category="navigation"),

    # Operations
    CommandEntry("status", "Show current system status overview.",
                 "status", aliases=("st", "s"), category="operations"),
    CommandEntry("summary", "Show operational summary.",
                 "summary", aliases=("su",), category="operations"),
    CommandEntry("locks", "Show active workspace locks.",
                 "locks", aliases=("lock",), category="operations"),

    # Actions
    CommandEntry("approve", "Approve a pending action.",
                 "approve <id> [reason]", aliases=("ap",), category="actions",
                 requires_mission=True, autocomplete_min_args=1),
    CommandEntry("reject", "Reject a pending action.",
                 "reject <id> [reason]", aliases=("rj",), category="actions",
                 requires_mission=True, autocomplete_min_args=1),
    CommandEntry("cancel", "Cancel a running mission.",
                 "cancel <id> [reason]", aliases=("cx",), category="actions",
                 requires_mission=True, autocomplete_min_args=1),
    CommandEntry("resume", "Resume a paused mission.",
                 "resume <id> [step]", aliases=("rs",), category="actions",
                 requires_mission=True, autocomplete_min_args=1),

    # Recommendations
    CommandEntry("execute", "Execute a recommendation.",
                 "execute <id>", aliases=("exec",), category="actions",
                 requires_approval=True, autocomplete_min_args=1),
    CommandEntry("simulate", "Simulate a recommendation.",
                 "simulate <id>", aliases=("sim",), category="actions",
                 autocomplete_min_args=1),

    # Utilities
    CommandEntry("help", "Show help for commands.",
                 "help [command]", aliases=("?",), category="utility"),
    CommandEntry("refresh", "Refresh the current view.",
                 "refresh [--force]", aliases=("r", "reload"), category="utility"),
    CommandEntry("query", "Ask a question about the system.",
                 "query <text>", aliases=("q", "ask"), category="utility",
                 autocomplete_min_args=1),
    CommandEntry("back", "Go back one screen.",
                 "back", aliases=("b",), category="navigation"),
    CommandEntry("exit", "Exit the console.",
                 "exit", aliases=("quit", "q"), category="utility"),
    CommandEntry("theme", "Switch console theme.",
                 "theme [dark|light|minimal]", aliases=(), category="utility"),
    CommandEntry("notifications", "View pending notifications.",
                 "notifications", aliases=("notifs", "notif"), category="operations"),
    CommandEntry("dismiss", "Dismiss a notification.",
                 "dismiss <id> [--all]", aliases=(), category="actions",
                 autocomplete_min_args=1),
]

# ── Pre-built lookups (immutable) ─────────────────────────────────────

COMMANDS: Tuple[CommandEntry, ...] = tuple(_COMMAND_LIST)
COMMAND_NAMES: FrozenSet[str] = frozenset(c.name for c in _COMMAND_LIST)

ALIASES: Dict[str, str] = {}
for _cmd in _COMMAND_LIST:
    for _alias in _cmd.aliases:
        ALIASES[_alias] = _cmd.name
ALIASES_FROZEN: Dict[str, str] = dict(ALIASES)  # dict copy, effectively immutable

_CATEGORIES: Dict[str, List[CommandEntry]] = {}
for _c in _COMMAND_LIST:
    _CATEGORIES.setdefault(_c.category, []).append(_c)
CATEGORIES: Dict[str, Tuple[CommandEntry, ...]] = {
    k: tuple(v) for k, v in _CATEGORIES.items()
}

_HELP_BY_NAME: Dict[str, str] = {c.name: c.help_text for c in _COMMAND_LIST}
_HELP_BY_ALIAS: Dict[str, str] = {}
for _c in _COMMAND_LIST:
    for _a in _c.aliases:
        _HELP_BY_ALIAS[_a] = _c.help_text


def get_command_help(name_or_alias: str) -> str:
    """Get help text for a command by name or alias."""
    name = ALIASES.get(name_or_alias, name_or_alias)
    entry = _HELP_BY_NAME.get(name)
    if entry:
        return entry
    return ""


def get_command_usage(name_or_alias: str) -> str:
    """Get usage string for a command by name or alias."""
    name = ALIASES.get(name_or_alias, name_or_alias)
    for c in _COMMAND_LIST:
        if c.name == name:
            return c.usage
    return ""


def get_command_aliases(name: str) -> Tuple[str, ...]:
    """Get aliases for a command by its canonical name."""
    for c in _COMMAND_LIST:
        if c.name == name:
            return c.aliases
    return ()


def get_autocomplete(name_or_alias: str) -> int:
    """Get autocomplete min args for a command."""
    name = ALIASES.get(name_or_alias, name_or_alias)
    for c in _COMMAND_LIST:
        if c.name == name:
            return c.autocomplete_min_args
    return 0


def get_all_commands() -> Tuple[CommandEntry, ...]:
    """Get all registered commands."""
    return COMMANDS


def get_commands_by_category(category: str) -> Tuple[CommandEntry, ...]:
    """Get all commands in a category."""
    return CATEGORIES.get(category, ())


def get_command(name_or_alias: str) -> Optional[CommandEntry]:
    """Get a command entry by name or alias. Returns None if not found."""
    resolved = ALIASES.get(name_or_alias, name_or_alias)
    for c in _COMMAND_LIST:
        if c.name == resolved:
            return c
    return None


def list_categories() -> Tuple[str, ...]:
    """Get all command categories."""
    return tuple(sorted(CATEGORIES.keys()))


def format_help(command: str = "") -> str:
    """Format help text for display. Returns a plain string.

    If command is empty, shows all commands grouped by category.
    """
    if command:
        resolved = ALIASES.get(command, command)
        entry = get_command(resolved)
        if not entry:
            return f"Unknown command: '{command}'"
        lines = [
            f"{entry.name}: {entry.help_text}",
            f"  Usage: {entry.usage}",
        ]
        if entry.aliases:
            lines.append(f"  Aliases: {', '.join(entry.aliases)}")
        lines.append(f"  Category: {entry.category}")
        return "\n".join(lines)

    pieces = []
    for cat in list_categories():
        pieces.append(f"\n[{cat}]")
        for cmd in CATEGORIES[cat]:
            pieces.append(f"  {cmd.name:<16s} {cmd.help_text}")
    return "\n".join(pieces)


class CommandRegistry:
    """Runtime registry wrapper around the static command definitions.

    Immutable: commands cannot be added, removed, or modified at runtime.
    """

    @property
    def commands(self) -> Tuple[CommandEntry, ...]:
        return COMMANDS

    @property
    def names(self) -> FrozenSet[str]:
        return COMMAND_NAMES

    @property
    def aliases(self) -> Dict[str, str]:
        return dict(ALIASES_FROZEN)

    def resolve(self, name_or_alias: str) -> Optional[str]:
        return ALIASES.get(name_or_alias, name_or_alias)

    def get(self, name_or_alias: str) -> Optional[CommandEntry]:
        return get_command(name_or_alias)

    def validate(self, name_or_alias: str) -> bool:
        return self.resolve(name_or_alias) in COMMAND_NAMES

    def get_category(self, name_or_alias: str) -> str:
        cmd = get_command(name_or_alias)
        return cmd.category if cmd else ""

    def autocomplete(self, partial: str) -> Tuple[str, ...]:
        """Return command names matching a partial string."""
        partial = partial.lower().strip()
        if not partial:
            return tuple(sorted(c.name for c in _COMMAND_LIST))
        matches: list = []
        for c in _COMMAND_LIST:
            if c.name.startswith(partial):
                matches.append(c.name)
            else:
                for alias in c.aliases:
                    if alias.startswith(partial) and alias not in matches:
                        matches.append(c.name)
                        break
        return tuple(sorted(matches))
