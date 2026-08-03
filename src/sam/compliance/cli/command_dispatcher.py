"""CommandDispatcher — parses CLI argv and dispatches to handlers.

The dispatcher is pure and deterministic: given the same argv it
always produces the same parsed command. It knows the command grammar:

    compliance run [--all | <check-id> | --level L0 | --category ADR
                    | --authority Specification | --tag runtime]
    compliance list [filters...]
    compliance info <check-id>
    compliance summary

It does NOT execute anything — it only parses and dispatches.
"""

from __future__ import annotations

from typing import List, Optional

from .session_runner import SessionFilter


class CommandParseError(Exception):
    """Raised when command-line arguments are malformed."""

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


# Supported commands.
RUN = "run"
LIST = "list"
INFO = "info"
SUMMARY = "summary"


class Command:
    """A parsed CLI command with its action and filter."""

    def __init__(
        self,
        action: str,
        check_id: Optional[str] = None,
        level: Optional[str] = None,
        category: Optional[str] = None,
        authority: Optional[str] = None,
        tag: Optional[str] = None,
    ):
        self.action = action
        self.check_id = check_id
        self.level = level
        self.category = category
        self.authority = authority
        self.tag = tag

    def to_filter(self) -> SessionFilter:
        """Convert to a SessionFilter (empty for --all / list-all)."""
        return SessionFilter(
            check_id=self.check_id,
            level=self.level,
            category=self.category,
            authority=self.authority,
            tag=self.tag,
        )

    def __repr__(self) -> str:
        return "Command(action=%s, check_id=%s, level=%s, category=%s, authority=%s, tag=%s)" % (
            self.action, self.check_id, self.level, self.category,
            self.authority, self.tag)


class CommandDispatcher:
    """Parses argv into a Command and dispatches to a handler.

    The dispatcher uses a handler registry keyed by action name.
    A default handler is invoked if no explicit handler is registered.
    """

    def __init__(self, handlers: Optional[dict] = None):
        """Build dispatcher.

        Args:
            handlers: Optional dict {action_name: callable(command)}.
                      Defaults to empty — dispatch returns the action
                      name if no handler registered.
        """
        self._handlers: dict = dict(handlers or {})

    # -- Parsing --------------------------------------------------------------

    def parse(self, argv: List[str]) -> Command:
        """Parse command-line arguments.

        Args:
            argv: Command arguments (not including program name).

        Returns:
            A Command.

        Raises:
            CommandParseError: If arguments are malformed.
        """
        if not argv:
            raise CommandParseError("No command provided")

        action = argv[0]
        if action not in (RUN, LIST, INFO, SUMMARY):
            raise CommandParseError("Unknown command: %s" % action)

        check_id = None
        level = None
        category = None
        authority = None
        tag = None

        i = 1
        while i < len(argv):
            token = argv[i]
            if token == "--all":
                # --all means no filter (all enabled checks)
                i += 1
            elif token == "--level":
                level = self._require_value(argv, i, "--level")
                i += 2
            elif token == "--category":
                category = self._require_value(argv, i, "--category")
                i += 2
            elif token == "--authority":
                authority = self._require_value(argv, i, "--authority")
                i += 2
            elif token == "--tag":
                tag = self._require_value(argv, i, "--tag")
                i += 2
            elif token.startswith("-"):
                raise CommandParseError("Unknown option: %s" % token)
            else:
                # Positional check-id
                if action != RUN and action != INFO:
                    raise CommandParseError(
                        "Unexpected positional argument: %s" % token)
                if check_id is not None:
                    raise CommandParseError(
                        "Multiple check ids provided: %s" % token)
                check_id = token
                i += 1

        # Info requires a check-id
        if action == INFO and check_id is None:
            raise CommandParseError("'info' requires a <check-id>")

        return Command(
            action=action,
            check_id=check_id,
            level=level,
            category=category,
            authority=authority,
            tag=tag,
        )

    # -- Dispatch -------------------------------------------------------------

    def dispatch(self, command: Command):
        """Dispatch a parsed command to its handler.

        Returns the handler result, or the action name if no handler
        is registered for that action.
        """
        handler = self._handlers.get(command.action)
        if handler is None:
            return command.action
        return handler(command)

    # -- Internals ------------------------------------------------------------

    def register(self, action: str, handler) -> None:
        """Register a handler callable for an action."""
        self._handlers[action] = handler

    @staticmethod
    def _require_value(argv: List[str], index: int, option: str) -> str:
        """Fetch the value for a flag option, raising if absent."""
        if index + 1 >= len(argv) or argv[index + 1].startswith("-"):
            raise CommandParseError("Option %s requires a value" % option)
        return argv[index + 1]
