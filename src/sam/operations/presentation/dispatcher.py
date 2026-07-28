"""CommandDispatcher — Routes Interaction Commands through Conversation API.

Does NOT call domain logic directly.
All commands are forwarded to Conversation API.
Support for validation, help, and history.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from datetime import datetime

from .interaction import (
    ApproveMission, RejectMission, CancelMission, ResumeMission,
    ExecuteRecommendation, SimulateRecommendation,
    OpenMission, OpenTimeline, OpenEvidence,
    RefreshDashboard, UserQuery,
)


COMMAND_TYPES = [
    "approve", "reject", "cancel", "resume",
    "execute", "simulate",
    "open_mission", "open_timeline", "open_evidence",
    "refresh", "query", "back", "home", "help", "exit",
]


COMMAND_HELP: Dict[str, str] = {
    "approve": "Approve a pending mission. Usage: approve <mission_id> [reason]",
    "reject": "Reject a pending mission. Usage: reject <mission_id> [reason]",
    "cancel": "Cancel a running mission. Usage: cancel <mission_id> [reason]",
    "resume": "Resume a paused mission. Usage: resume <mission_id> [from_step]",
    "execute": "Execute a recommendation. Usage: execute <rec_id>",
    "simulate": "Simulate a recommendation. Usage: simulate <rec_id>",
    "open_mission": "View mission details. Usage: open_mission <mission_id>",
    "open_timeline": "View timeline. Usage: open_timeline [filter]",
    "open_evidence": "View evidence. Usage: open_evidence <evidence_id> [mission_id]",
    "refresh": "Refresh the current view. Usage: refresh [--force]",
    "query": "Ask a question. Usage: query <text>",
    "back": "Go back one screen.",
    "home": "Go to dashboard.",
    "help": "Show this help message. Usage: help [command]",
    "exit": "Exit the console.",
}


@dataclass
class CommandResult:
    """Result of processing a command."""
    success: bool = True
    message: str = ""
    command_type: str = ""
    screen_change: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class CommandHistory:
    """Immutable command history entry."""
    command: str = ""
    args: str = ""
    result: str = ""
    timestamp: str = ""


class CommandDispatcher:
    """Dispatches commands to the Conversation API.

    The dispatcher does NOT execute domain logic.
    It validates commands, converts them to Interaction Contract objects,
    and forwards them to a registered handler (typically Conversation API).

    Thread-safe: no mutable shared state beyond _history.
    """

    def __init__(self, handler: Optional[Callable] = None) -> None:
        self._handler: Optional[Callable] = handler
        self._history: list = []

    @property
    def history(self) -> Tuple[CommandHistory, ...]:
        return tuple(self._history[-50:])

    def set_handler(self, handler: Callable) -> None:
        """Set the Conversation API handler."""
        self._handler = handler

    # ── Main dispatch ─────────────────────────────────────────────────

    def dispatch(self, command: str, args: str = "") -> CommandResult:
        """Parse and dispatch a command string to the handler.

        Command format:
            approve <mission_id> [reason]
            query what's happening?
            refresh [--force]
            help [command]
        """
        result = self._execute(command, args)
        self._history.append(CommandHistory(
            command=command, args=args,
            result=result.message, timestamp=result.timestamp,
        ))
        return result

    def dispatch_interaction(self, interaction: Any) -> CommandResult:
        """Dispatch an Interaction Contract object directly."""
        if self._handler is None:
            return CommandResult(success=False, message="No handler registered.",
                                 command_type="error")

        cmd_type = type(interaction).__name__.lower()
        try:
            response = self._handler(interaction)
            return CommandResult(
                success=True,
                command_type=cmd_type,
                message=str(response) if response else "OK",
            )
        except Exception as e:
            return CommandResult(
                success=False,
                command_type=cmd_type,
                message=f"Error: {e}",
            )

    # ── Validation ────────────────────────────────────────────────────

    def validate(self, command: str, args: str = "") -> CommandResult:
        """Validate a command without executing it."""
        cmd = command.strip().lower()

        if cmd not in COMMAND_TYPES:
            return CommandResult(
                success=False,
                message=f"Unknown command: '{cmd}'. Type 'help' for available commands.",
                command_type="error",
            )

        # Validate required args for specific commands
        if cmd in ("approve", "reject", "cancel", "resume", "open_mission")\
           and not args.strip():
            return CommandResult(
                success=False,
                message=f"'{cmd}' requires a mission_id. Usage: {cmd} <mission_id>",
                command_type="error",
            )

        if cmd in ("execute", "simulate", "open_evidence") and not args.strip():
            return CommandResult(
                success=False,
                message=f"'{cmd}' requires an id. Usage: {cmd} <id>",
                command_type="error",
            )

        if cmd == "query" and not args.strip():
            return CommandResult(
                success=False,
                message="'query' requires text. Usage: query <your question>",
                command_type="error",
            )

        return CommandResult(success=True, message="Command valid.", command_type=cmd)

    # ── Help ──────────────────────────────────────────────────────────

    def help(self, command: str = "") -> str:
        """Get help text for a command or all commands."""
        if command:
            cmd = command.strip().lower()
            if cmd in COMMAND_HELP:
                return COMMAND_HELP[cmd]
            return f"Unknown command: '{cmd}'. Type 'help' for available commands."

        lines = ["Available commands:", ""]
        for cmd, help_text in COMMAND_HELP.items():
            short = help_text.split(".")[0]
            lines.append(f"  {cmd:20s} — {short}")
        lines.extend([
            "",
            "Type 'help <command>' for detailed usage.",
            "Shortcuts: 1-8 for screens, R=refresh, Q=exit, ?=help",
        ])
        return "\n".join(lines)

    # ── History ───────────────────────────────────────────────────────

    def last_history(self, n: int = 10) -> Tuple[CommandHistory, ...]:
        """Get last N history entries."""
        return tuple(self._history[-n:])

    # ── Internal ──────────────────────────────────────────────────────

    def _execute(self, command: str, args: str) -> CommandResult:
        """Execute a parsed command."""
        cmd = command.strip().lower()
        args = args.strip()

        # Validate first
        validation = self.validate(cmd, args)
        if not validation.success:
            return validation

        # Handle built-in commands (no handler needed)
        if cmd == "help":
            return CommandResult(
                success=True, message=self.help(args), command_type="help",
            )
        if cmd == "exit":
            return CommandResult(
                success=True, message="Exiting...", command_type="exit",
                screen_change="exit",
            )
        if cmd == "back":
            return CommandResult(
                success=True, message="Going back.", command_type="back",
                screen_change="back",
            )
        if cmd == "home":
            return CommandResult(
                success=True, message="Going to dashboard.", command_type="home",
                screen_change="dashboard",
            )

        # Build Interaction Contract object
        interaction = self._build_interaction(cmd, args)
        if interaction is None:
            return CommandResult(
                success=False, message=f"Failed to build command: {cmd}",
                command_type="error",
            )

        # Forward to handler
        if self._handler is None:
            return CommandResult(
                success=False, message="No handler registered. Cannot execute commands.",
                command_type="error",
            )

        try:
            response = self._handler(interaction)
            return CommandResult(
                success=True, command_type=cmd,
                message=str(response) if response else f"{cmd} executed.",
            )
        except Exception as e:
            return CommandResult(
                success=False, command_type=cmd,
                message=f"Error executing '{cmd}': {e}",
            )

    def _build_interaction(self, cmd: str, args: str) -> Any:
        """Convert command string to Interaction Contract object."""
        parts = args.split()

        if cmd == "approve":
            return ApproveMission(mission_id=parts[0], reason=" ".join(parts[1:]))

        if cmd == "reject":
            return RejectMission(mission_id=parts[0], reason=" ".join(parts[1:]))

        if cmd == "cancel":
            return CancelMission(mission_id=parts[0], reason=" ".join(parts[1:]))

        if cmd == "resume":
            return ResumeMission(
                mission_id=parts[0],
                from_step=parts[1] if len(parts) > 1 else None,
            )

        if cmd == "execute":
            return ExecuteRecommendation(recommendation_id=parts[0])

        if cmd == "simulate":
            return SimulateRecommendation(recommendation_id=parts[0])

        if cmd == "open_mission":
            return OpenMission(mission_id=parts[0])

        if cmd == "open_timeline":
            return OpenTimeline(filter_type=args)

        if cmd == "open_evidence":
            return OpenEvidence(
                evidence_id=parts[0],
                source_mission=parts[1] if len(parts) > 1 else "",
            )

        if cmd == "refresh":
            return RefreshDashboard(force="--force" in args)

        if cmd == "query":
            return UserQuery(text=args, context="console")

        return None
