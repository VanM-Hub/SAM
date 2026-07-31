"""Shell Provider — adapter shell preview (Phase XIV)."""
from .shell_provider import ShellProvider
from .command_builder import ShellCommand, ShellCommandBuilder
from .command_preview import ShellPreview, ShellCommandPreview
from .command_validator import ShellCommandValidator, ShellCommandValidation
from .command_history import ShellHistory, ShellHistoryEntry
from .conversation_shell import ConversationShellBridge
from .dashboard_shell import DashboardShellBridge

__all__ = [
    "ShellProvider",
    "ShellCommand",
    "ShellCommandBuilder",
    "ShellPreview",
    "ShellCommandPreview",
    "ShellCommandValidator",
    "ShellCommandValidation",
    "ShellHistory",
    "ShellHistoryEntry",
    "ConversationShellBridge",
    "DashboardShellBridge",
]
