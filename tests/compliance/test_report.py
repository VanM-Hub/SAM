"""Tests for ComplianceReport, report builder, and text reporter."""

from sam.compliance import (
    ComplianceRegistry,
    ComplianceEngine,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceCategory,
    EvidenceType,
    Severity,
    ComplianceReport,
    ComplianceVerdict,
    VerdictGrade,
    LevelSummary,
    CategorySummary,
    TextReporter,
)
from sam.compliance.reporters.report_builder import ReportBuilder


def _make_check(check_id, level=ComplianceLevel.L0_STRUCTURAL,
                execution_fn=None, severity=None, category=None):
    return ComplianceCheck(
        check_id=check_id,
        level=level,
        category=category or ComplianceCategory.RUNTIME_UNITS,
        description="Test check %s" % check_id,
        evidence_type=EvidenceType.FILE_EXISTS,
        severity=severity or Severity.MAJOR,
        baseline_ref="TEST_REF",
        execution_fn=execution_fn,
    )


class TestLevelSummary:
    """LevelSummary model."""

    def test_level_summary_all_pass(self):
        ls = LevelSummary(
            level=ComplianceLevel.L0_STRUCTURAL,
            total_checks=5, passed=5, failed=0, skipped=0,
        )
        assert ls.is_pass

    def test_level_summary_has_failures(self):
        ls = LevelSummary(
            level=ComplianceLevel.L1_SPECIFICATION,
            total_checks=10, passed=9, failed=1, skipped=0,
        )
        assert not ls.is_pass


class TestCategorySummary:
    """CategorySummary model."""

    def test_category_summary_total(self):
        cs = CategorySummary(
            category=ComplianceCategory.ADR,
            critical_count=1, major_count=2, minor_count=3, info_count=1,
        )
        assert cs.total_findings == 7


class TestReportData:
    """Report data correctness."""

    def test_report_verdict_structure(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "baseline")

        assert isinstance(report, ComplianceReport)
        assert isinstance(report.verdict, ComplianceVerdict)
        assert report.runtime_identity == "target"
        assert report.baseline_ref == "baseline"
        assert report.suite_version == "P1-001"
        assert report.verdict_label == "Certified"

    def test_report_level_summaries(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("L0-01", level=ComplianceLevel.L0_STRUCTURAL,
                                 execution_fn=lambda: True))
        reg.register(_make_check("L1-01", level=ComplianceLevel.L1_SPECIFICATION,
                                 execution_fn=lambda: True))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "baseline")

        assert "L0" in report.level_summaries
        assert "L1" in report.level_summaries
        assert report.level_summaries["L0"].is_pass
        assert report.level_summaries["L1"].is_pass

    def test_report_category_summaries(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", category=ComplianceCategory.ADR,
                                 execution_fn=lambda: False,
                                 severity=Severity.MAJOR))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "baseline")

        cs = report.category_summaries.get("ADR")
        assert cs is not None
        assert cs.major_count >= 1

    def test_report_findings_ordered(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("Z02", execution_fn=lambda: False))
        reg.register(_make_check("A01", execution_fn=lambda: False))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "baseline")

        finding_ids = [f.check_id for f in report.findings]
        assert finding_ids == sorted(finding_ids)


class TestReportBuilder:
    """ReportBuilder functionality."""

    def test_build_report(self):
        report = ReportBuilder.build(
            session_id="sess-1",
            runtime_identity="test-rt",
            timestamp="2026-08-03T14:00:00Z",
            baseline_ref="abc123",
            suite_version="P1-001",
            verdict=ComplianceVerdict.compute(0, 0, 0),
            level_summaries={},
            category_summaries={},
            findings=[],
            evidence=[],
            total_checks=10,
            total_executed=10,
            total_passed=10,
            total_failed=0,
            total_skipped=0,
            duration_seconds=2.5,
        )
        assert report.session_id == "sess-1"
        assert report.runtime_identity == "test-rt"
        assert report.verdict.grade == VerdictGrade.A_CERTIFIED
        assert report.total_checks == 10
        assert report.total_passed == 10
        assert report.duration_seconds == 2.5


class TestTextReporter:
    """Text reporter output."""

    def test_format_empty_report(self):
        report = ReportBuilder.build(
            session_id="sess-1",
            runtime_identity="test-rt",
            timestamp="2026-08-03T14:00:00Z",
            baseline_ref="abc123",
            suite_version="P1-001",
            verdict=ComplianceVerdict.compute(0, 0, 0),
            level_summaries={},
            category_summaries={},
            findings=[],
            evidence=[],
            total_checks=0, total_executed=0,
            total_passed=0, total_failed=0, total_skipped=0,
            duration_seconds=0.0,
        )
        output = TextReporter.format(report)
        assert "RUNTIME COMPLIANCE REPORT" in output
        assert "OVERALL VERDICT:  A — Certified" in output
        assert "test-rt" in output
        assert "REPORT COMPLETE" in output

    def test_format_with_findings(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", severity=Severity.CRITICAL,
                                 execution_fn=lambda: False))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "baseline")

        output = TextReporter.format(report)
        assert "D — Not Compliant" in output
        assert "CRITICAL:  1" in output
        assert "FINDINGS DETAIL" in output

    def test_format_deterministic(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "baseline")

        out1 = TextReporter.format(report)
        out2 = TextReporter.format(report)
        assert out1 == out2


class TestReportStateless:
    """Report is immutable and stateless."""

    def test_report_frozen(self):
        report = ComplianceReport(
            session_id="s-1",
            runtime_identity="rt",
            timestamp="ts",
            baseline_ref="br",
            suite_version="P1-001",
            verdict=ComplianceVerdict.compute(0, 0, 0),
        )
        assert report.session_id == "s-1"

    def test_report_to_dict(self):
        report = ComplianceReport(
            session_id="s-1",
            runtime_identity="rt",
            timestamp="ts",
            baseline_ref="br",
            suite_version="P1-001",
            verdict=ComplianceVerdict.compute(0, 0, 0),
        )
        d = report.to_dict()
        assert d["session_id"] == "s-1"
        assert d["verdict"]["label"] == "Certified"
