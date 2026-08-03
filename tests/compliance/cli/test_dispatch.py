"""CLI dispatch + manifest ordering tests for the Compliance CLI."""

import io
import contextlib

import pytest

from sam.compliance.cli import ComplianceCLI


def _capture(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn()
    return buf.getvalue()


class TestCLIDispatch:
    def test_run_dispatch_all(self, cli):
        text = _capture(lambda: cli.execute_safe(["run"]))
        assert "executed_checks : 99" in text

    def test_run_dispatch_level(self, cli):
        text = _capture(lambda: cli.execute_safe(["run", "--level", "L0"]))
        assert "executed_checks : 12" in text

    def test_run_dispatch_check_id(self, cli):
        text = _capture(lambda: cli.execute_safe(["run", "L0-01"]))
        assert "executed_checks : 1" in text

    def test_list_dispatch(self, cli):
        text = _capture(lambda: cli.execute_safe(["list"]))
        assert "Compliance Checks (99)" in text

    def test_summary_dispatch(self, cli):
        text = _capture(lambda: cli.execute_safe(["summary"]))
        assert "manifest_entries  : 99" in text

    def test_info_dispatch(self, cli):
        text = _capture(lambda: cli.execute_safe(["info", "L0-01"]))
        assert "Check: L0-01" in text

    def test_execute_returns_verdict_code(self, cli):
        code = cli.execute(["run"])
        assert code == 0

    def test_execute_parse_error_raises(self, cli):
        from sam.compliance.cli import CommandParseError
        with pytest.raises(CommandParseError):
            cli.execute(["bogus"])


class TestManifestOrderingRespected:
    def test_run_honors_disabled_checks(self, cli):
        """Disabling a check via manifest reduces executed count."""
        from sam.compliance.manifest import ManifestLoader
        from sam.compliance.cli import ComplianceCLI
        from sam.compliance.catalog import ComplianceCheckCatalog
        cat = cli._catalog
        manifest = ManifestLoader(cat).load(
            overrides={"L0-01": {"enabled": False},
                       "L0-02": {"enabled": False}})
        custom_cli = ComplianceCLI(manifest=manifest, catalog=cat)
        text = _capture(lambda: custom_cli.execute_safe(["run"]))
        assert "executed_checks : 97" in text
        assert "skipped_checks  : 2" in text

    def test_runner_uses_manifest_entries_order(self, runner):
        """enabled() returns manifest-ordered entries (order, id)."""
        entries = runner._manifest.enabled()
        for i in range(1, len(entries)):
            a = (entries[i - 1].execution_order, entries[i - 1].check_id)
            b = (entries[i].execution_order, entries[i].check_id)
            assert a <= b

    def test_run_check_id_respects_manifest(self, cli):
        """Running a disabled check id yields 0 executed (not executed)."""
        from sam.compliance.manifest import ManifestLoader
        from sam.compliance.cli import ComplianceCLI
        cat = cli._catalog
        manifest = ManifestLoader(cat).load(
            overrides={"L0-01": {"enabled": False}})
        custom_cli = ComplianceCLI(manifest=manifest, catalog=cat)
        text = _capture(lambda: custom_cli.execute_safe(["run", "L0-01"]))
        # Disabled check -> 0 selected
        assert "executed_checks : 0" in text
