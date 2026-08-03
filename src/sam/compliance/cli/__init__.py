"""Compliance CLI (P1-006) — executable compliance tool.

Transforms the Compliance Engine into an executable tool. After
P1-006 the whole compliance suite can be run via one command.

The CLI does NOT implement the 99 checkers. It only runs registered
checks (placeholder or real) via the SessionRunner.

Commands:
    compliance run        -- run compliance session (-all/filters)
    compliance list       -- list checks
    compliance info <id>  -- show check metadata
    compliance summary    -- show catalog/manifest statistics
"""

from .command_dispatcher import (
    CommandDispatcher, Command, CommandParseError,
    RUN, LIST, INFO, SUMMARY,
)
from .session_runner import (
    SessionRunner, SessionResult, SessionFilter,
)
from .console_reporter import ConsoleReporter
from .exit_code_resolver import ExitCodeResolver
from .compliance_cli import ComplianceCLI, main

__all__ = [
    # Dispatcher
    "CommandDispatcher",
    "Command",
    "CommandParseError",
    "RUN",
    "LIST",
    "INFO",
    "SUMMARY",
    # Runner
    "SessionRunner",
    "SessionResult",
    "SessionFilter",
    # Reporter
    "ConsoleReporter",
    # Exit codes
    "ExitCodeResolver",
    # CLI
    "ComplianceCLI",
    "main",
]
