"""
Console Runtime — Operational Console for SAM.

Sprint 14: Runtime infrastructure (Lifecycle, Registry, Prompt, Event Bus,
Notification Center, Shortcuts, Config, Error Recovery, Telemetry).
Sprint 15: Operational features (Dashboard, Mission Monitor, Approval
Workspace, Timeline Explorer, Notification Workspace, Status Bar,
Log Viewer, Session Workspace).

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
from .dashboard_runtime import (
    DashboardRuntime, RefreshMode, FilterState,
)
from .mission_monitor import (
    MissionMonitor, MissionEntry, MissionMonitorFactory,
)
from .approval_workspace import (
    ApprovalWorkspace, ApprovalItem, ApprovalAction,
    ApprovalDispatcher, ApprovalWorkspaceFactory,
)
from .timeline_explorer import (
    TimelineExplorer, TimelineEntry, TimelineExplorerFactory,
)
from .notification_workspace import (
    NotificationWorkspace, NotificationItem as NotifItem,
)
from .status_bar import (
    StatusBar, StatusBarFactory,
)
from .log_viewer import (
    LogViewer, LogEntry, LogViewerFactory,
)
from .session_workspace import (
    SessionWorkspace, SessionWorkspaceFactory,
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
    # OP-191: Dashboard Runtime
    "DashboardRuntime", "RefreshMode", "FilterState",
    # OP-192: Mission Monitor
    "MissionMonitor", "MissionEntry", "MissionMonitorFactory",
    # OP-193: Approval Workspace
    "ApprovalWorkspace", "ApprovalItem", "ApprovalAction",
    "ApprovalDispatcher", "ApprovalWorkspaceFactory",
    # OP-194: Timeline Explorer
    "TimelineExplorer", "TimelineEntry", "TimelineExplorerFactory",
    # OP-195: Notification Workspace
    "NotificationWorkspace",
    # OP-196: Status Bar
    "StatusBar", "StatusBarFactory",
    # OP-197: Log Viewer
    "LogViewer", "LogEntry", "LogViewerFactory",
    # OP-198: Session Workspace
    "SessionWorkspace", "SessionWorkspaceFactory",
]
