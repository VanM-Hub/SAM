"""
Console Runtime — Operational Console for SAM.

Sprint 14: Runtime infrastructure (Lifecycle, Registry, Prompt, Event Bus,
Notification Center, Shortcuts, Config, Error Recovery, Telemetry).

All modules in this package are runtime support for the SAM Console.
No business logic. No domain imports. No database access.
"""

from __future__ import annotations

from .app import (
    ConsoleApp, AppState, AppConfig,
)
from .command_registry import (
    CommandRegistry, CommandEntry, COMMANDS, ALIASES,
    get_command_help, get_command_aliases, get_autocomplete,
    format_help, list_categories, get_commands_by_category,
)
from .prompt_runtime import (
    PromptRuntime, PromptResult,
)
from .event_bus import (
    EventBus, ScreenChanged, CommandExecuted, RefreshRequested,
    MissionSelected, NotificationRaised, ThemeChanged,
    ErrorOccurred, ShutdownRequested,
)
from .notification_center import (
    NotificationCenter, NotificationItem,
)
from .shortcut import (
    ShortcutRegistry, ShortcutEntry, SHORTCUTS,
)
from .config import (
    ConsoleConfig, CONSOLE_DEFAULTS,
)
from .recovery import (
    ErrorRecovery, RecoveryStrategy,
)
from .telemetry import (
    ConsoleTelemetry, TelemetrySnapshot,
)

__all__ = [
    # OP-181: App Lifecycle
    "ConsoleApp", "AppState", "AppConfig",
    # OP-182: Command Registry
    "CommandRegistry", "CommandEntry", "COMMANDS", "ALIASES",
    "get_command_help", "get_command_aliases", "get_autocomplete",
    "format_help", "list_categories", "get_commands_by_category",
    # OP-183: Prompt Runtime
    "PromptRuntime", "PromptResult",
    # OP-184: Event Bus
    "EventBus", "ScreenChanged", "CommandExecuted", "RefreshRequested",
    "MissionSelected", "NotificationRaised", "ThemeChanged",
    "ErrorOccurred", "ShutdownRequested",
    # OP-185: Notification Center
    "NotificationCenter", "NotificationItem",
    # OP-186: Shortcut Registry
    "ShortcutRegistry", "ShortcutEntry", "SHORTCUTS",
    # OP-187: Config
    "ConsoleConfig", "CONSOLE_DEFAULTS",
    # OP-188: Error Recovery
    "ErrorRecovery", "RecoveryStrategy",
    # OP-189: Console Telemetry
    "ConsoleTelemetry", "TelemetrySnapshot",
]
