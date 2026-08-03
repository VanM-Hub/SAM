"""ComplianceCLI — public entry point for the compliance CLI.

Wires the manifest, catalog, runner, dispatcher, reporter, and
exit-code resolver into a single executable interface:

    compliance run [--all | <check-id> | --level L0 | --category ADR
                    | --authority Specification | --tag runtime]
    compliance list [filters...]
    compliance info <check-id>
    compliance summary

The CLI is deterministic and respects the manifest + catalog +
runner as the single source of execution configuration.
"""

from __future__ import annotations

from typing import List, Optional

from ..catalog.catalog import ComplianceCheckCatalog
from ..manifest.manifest import ComplianceManifest
from .command_dispatcher import (
    CommandDispatcher, Command, CommandParseError, RUN, LIST, INFO, SUMMARY,
)
from .session_runner import SessionRunner, SessionFilter, SessionResult
from .console_reporter import ConsoleReporter
from .exit_code_resolver import ExitCodeResolver

# Reasonable defaults matching the compliance engine.
DEFAULT_TARGET = "runtime"
DEFAULT_BASELINE = "HEAD"
DEFAULT_SUITE = "P1-001"


class ComplianceCLI:
    """High-level CLI facade over the compliance subsystem."""

    def __init__(
        self,
        manifest: Optional[ComplianceManifest] = None,
        catalog: Optional[ComplianceCheckCatalog] = None,
    ) -> None:
        """Build CLI.

        Args:
            manifest: The manifest to use. If None, a fresh catalog
                      is loaded and a manifest built from it.
            catalog: The catalog to use. If None, a fresh one is loaded.
        """
        self._catalog = catalog if catalog is not None else ComplianceCheckCatalog()
        if manifest is not None:
            self._manifest = manifest
        else:
            from .session_runner import SessionRunner as _SR  # noqa
            from ..manifest.manifest import ComplianceManifest as _CM
            from ..manifest.loader import ManifestLoader
            loader = ManifestLoader(self._catalog)
            self._manifest = loader.load()

        self._runner = SessionRunner(self._manifest, self._catalog)
        self._dispatcher = CommandDispatcher()
        self._register_handlers()
        self._reporter = ConsoleReporter()
        self._exit_codes = ExitCodeResolver()

    # -- Public entry ---------------------------------------------------------

    def execute(self, argv: List[str]) -> int:
        """Execute a CLI command line.

        Args:
            argv: Command arguments (not including program name).

        Returns:
            Process exit code (0..3). 0 = success/certified.

        Raises:
            CommandParseError: On malformed arguments.
        """
        command = self._dispatcher.parse(argv)
        return self._dispatch_command(command)

    def execute_safe(self, argv: List[str]) -> int:
        """Execute but convert parse errors to a readable message + code.

        Returns exit code 0 for success, 2 for usage/parse errors,
        and the verdict code for run commands.
        """
        try:
            return self.execute(argv)
        except CommandParseError as e:
            print("error: %s" % e.message)
            return 2
        except KeyError as e:
            print("error: %s" % e)
            return 2

    # -- Internal: dispatch ---------------------------------------------------

    def _dispatch_command(self, command: Command) -> int:
        """Dispatch a command to the concrete handler and return exit code."""
        if command.action == RUN:
            result = self._runner.run(
                target_runtime=DEFAULT_TARGET,
                baseline_commit=DEFAULT_BASELINE,
                suite_version=DEFAULT_SUITE,
                check_filter=command.to_filter(),
            )
            print(self._reporter.report_run(result))
            return self._exit_codes.resolve(result.report.verdict.grade)

        if command.action == LIST:
            checks = self._runner.list_checks(command.to_filter())
            print(self._reporter.report_list(checks, command.to_filter()))
            return 0

        if command.action == INFO:
            return self._handle_info(command.check_id)

        if command.action == SUMMARY:
            print(self._reporter.report_summary(self._manifest, self._catalog))
            return 0

        # Unknown action — no handler
        print("error: unhandled command: %s" % command.action)
        return 2

    def _handle_info(self, check_id: str) -> int:
        """Render metadata for a check. Returns 0 if found, 1 if not."""
        metadata = self._catalog.get(check_id)
        if metadata is None:
            print("error: unknown check: %s" % check_id)
            return 1
        entry = self._manifest.get(check_id)
        enabled = entry.enabled if entry is not None else False
        print(self._reporter.report_info(metadata, enabled))
        return 0

    # -- Internal: handler registration --------------------------------------

    def _register_handlers(self) -> None:
        """Register the concrete handlers with the dispatcher.

        Handlers delegate to the private dispatch methods; the
        public execute() path uses _dispatch_command directly.
        """
        self._dispatcher.register(RUN, self._handle_run)
        self._dispatcher.register(LIST, self._handle_list)
        self._dispatcher.register(INFO, self._handle_info_cmd)
        self._dispatcher.register(SUMMARY, self._handle_summary)

    def _handle_run(self, command: Command):
        result = self._runner.run(
            target_runtime=DEFAULT_TARGET,
            baseline_commit=DEFAULT_BASELINE,
            suite_version=DEFAULT_SUITE,
            check_filter=command.to_filter(),
        )
        return self._reporter.report_run(result)

    def _handle_list(self, command: Command):
        checks = self._runner.list_checks(command.to_filter())
        return self._reporter.report_list(checks, command.to_filter())

    def _handle_info_cmd(self, command: Command):
        return self._handle_info(command.check_id)

    def _handle_summary(self, command: Command):
        return self._reporter.report_summary(self._manifest, self._catalog)


def main(argv=None) -> int:
    """Console-script entry point (used by `compliance` command)."""
    import sys
    if argv is None:
        argv = sys.argv[1:]
    cli = ComplianceCLI()
    return cli.execute_safe(list(argv))
