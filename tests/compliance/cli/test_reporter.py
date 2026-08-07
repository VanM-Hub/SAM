"""Reporter formatting + determinism tests for the Compliance CLI."""

import io
import contextlib

import pytest

from sam.compliance.cli.session_runner import SessionFilter
from sam.compliance.cli import ConsoleReporter


def _capture(fn):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        fn()
    return buf.getvalue()


class TestReporterRun:
    def test_report_run_contains_session_fields(self, runner):
        reporter = ConsoleReporter()
        result = runner.run()
        text = reporter.report_run(result)
        assert "session_id" in text
        assert "started_at" in text
        assert "completed_at" in text
        assert "executed_checks" in text
        assert "skipped_checks" in text

    def test_report_run_contains_statistics(self, runner):
        reporter = ConsoleReporter()
        text = reporter.report_run(runner.run())
        assert "Statistics" in text
        assert "passed" in text
        assert "failed" in text

    def test_report_run_contains_verdict(self, runner):
        reporter = ConsoleReporter()
        text = reporter.report_run(runner.run())
        assert "Verdict" in text
        assert "CERTIFIED" in text


class TestReporterList:
    def test_report_list_99(self, runner):
        reporter = ConsoleReporter()
        checks = runner.list_checks()
        text = reporter.report_list(checks)
        assert "Compliance Checks (99)" in text

    def test_report_list_filtered(self, runner):
        reporter = ConsoleReporter()
        checks = runner.list_checks(SessionFilter(level="L0"))
        text = reporter.report_list(checks)
        assert "Compliance Checks (12)" in text

    def test_report_list_deterministic(self, runner):
        reporter = ConsoleReporter()
        checks = runner.list_checks()
        a = reporter.report_list(checks)
        b = reporter.report_list(checks)
        assert a == b


class TestReporterInfo:
    def test_report_info_has_fields(self, runner):
        reporter = ConsoleReporter()
        metadata = runner._catalog.get("L1-C01")
        text = reporter.report_info(metadata, enabled=True)
        assert "L1-C01" in text
        assert "manifest_status" in text
        assert "enabled" in text


class TestReporterSummary:
    def test_report_summary_has_counts(self, runner):
        reporter = ConsoleReporter()
        text = reporter.report_summary(runner._manifest, runner._catalog)
        assert "catalog_checks" in text
        assert "manifest_entries" in text
        assert "By Level" in text
        assert "By Authority" in text


class TestDeterminism:
    def test_two_runs_same_structure(self, runner):
        """Session IDs differ (unique) but report body is deterministic
        because all placeholders produce inconclusive evidence."""
        reporter = ConsoleReporter()
        r1 = runner.run()
        r2 = runner.run()
        t1 = reporter.report_run(r1)
        t2 = reporter.report_run(r2)
        # Strip session_id lines (unique) and compare the rest
        def strip_session(text):
            return [l for l in text.splitlines() if "session_id" not in l
                    and "started_at" not in l and "completed_at" not in l
                    and "duration" not in l]
        assert strip_session(t1) == strip_session(t2)

    def test_list_stable_across_calls(self, cli):
        t1 = _capture(lambda: cli.execute_safe(["list"]))
        t2 = _capture(lambda: cli.execute_safe(["list"]))
        assert t1 == t2

    def test_summary_stable_across_calls(self, cli):
        t1 = _capture(lambda: cli.execute_safe(["summary"]))
        t2 = _capture(lambda: cli.execute_safe(["summary"]))
        assert t1 == t2

    def test_info_stable_across_calls(self, cli):
        t1 = _capture(lambda: cli.execute_safe(["info", "L2-01"]))
        t2 = _capture(lambda: cli.execute_safe(["info", "L2-01"]))
        assert t1 == t2
