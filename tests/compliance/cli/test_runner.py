"""Runner execution + session lifecycle tests for the Compliance CLI."""

import pytest

from sam.compliance.cli.session_runner import SessionFilter


class TestRunnerAll:
    def test_run_all_executes_99(self, runner):
        result = runner.run()
        assert result.executed_checks == 99
        assert result.skipped_checks == 0
        assert result.total_checks == 99

    def test_run_all_report_total_99(self, runner):
        result = runner.run()
        assert result.report.total_checks == 99
        assert result.report.total_executed == 99

    def test_result_has_session_fields(self, runner):
        result = runner.run()
        assert result.session_id
        assert result.started_at
        assert result.completed_at
        assert result.verdict in ("A", "B", "C", "D")

    def test_result_to_dict(self, runner):
        result = runner.run()
        d = result.to_dict()
        assert d["executed_checks"] == 99
        assert "session_id" in d
        assert "verdict" in d


class TestRunnerFilters:
    def test_run_level_l0(self, runner):
        result = runner.run(check_filter=SessionFilter(level="L0"))
        assert result.executed_checks == 12

    def test_run_level_l1(self, runner):
        result = runner.run(check_filter=SessionFilter(level="L1"))
        assert result.executed_checks == 40

    def test_run_level_l2(self, runner):
        result = runner.run(check_filter=SessionFilter(level="L2"))
        assert result.executed_checks == 17

    def test_run_category_adr(self, runner):
        result = runner.run(check_filter=SessionFilter(category="ADR"))
        assert result.executed_checks == 17

    def test_run_authority_specification(self, runner):
        result = runner.run(check_filter=SessionFilter(authority="Specification"))
        assert result.executed_checks == 47

    def test_run_tag_adr(self, runner):
        result = runner.run(check_filter=SessionFilter(tag="adr"))
        assert result.executed_checks == 17

    def test_run_single_check(self, runner):
        result = runner.run(check_filter=SessionFilter(check_id="L0-01"))
        assert result.executed_checks == 1

    def test_run_unknown_check_raises(self, runner):
        with pytest.raises(KeyError):
            runner.run(check_filter=SessionFilter(check_id="NOPE"))

    def test_run_combined_filters_and(self, runner):
        # L1 + Testing category -> deterministic intersection
        result = runner.run(check_filter=SessionFilter(level="L1", category="Testing"))
        # Count checks that satisfy BOTH
        ids = set()
        for c in runner._catalog.list_all():
            if c.level.value == "L1" and c.category.value == "Testing":
                ids.add(c.check_id)
        assert result.executed_checks == len(ids)


class TestSessionLifecycle:
    def test_disabled_checks_skipped(self, manifest, runner):
        """Disabled manifest entries are never executed."""
        # Disable L0-01 via a custom manifest
        from sam.compliance.manifest import ManifestLoader
        from sam.compliance.cli.session_runner import SessionRunner
        custom = ManifestLoader(runner._catalog).load(
            overrides={"L0-01": {"enabled": False}})
        r = SessionRunner(custom, runner._catalog).run()
        assert r.executed_checks == 98
        assert r.skipped_checks == 1

    def test_skipped_equals_manifest_minus_executed(self, runner):
        result = runner.run(check_filter=SessionFilter(level="L3"))
        assert result.executed_checks == 22
        assert result.skipped_checks == 99 - 22

    def test_engine_state_advances(self, runner):
        result = runner.run()
        # Engine is immutable after ARCHIVED at end of run_session
        report = result.report
        assert report.findings is not None
        assert report.verdict is not None


class TestListChecks:
    def test_list_all_99(self, runner):
        checks = runner.list_checks()
        assert len(checks) == 99

    def test_list_by_level(self, runner):
        checks = runner.list_checks(SessionFilter(level="L4"))
        assert len(checks) == 8

    def test_list_by_tag(self, runner):
        checks = runner.list_checks(SessionFilter(tag="structural"))
        assert len(checks) >= 1

    def test_list_empty_filter_all(self, runner):
        assert len(runner.list_checks(SessionFilter())) == 99
