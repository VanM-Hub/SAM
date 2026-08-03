"""Tests for check execution and evidence collection."""

import pytest
from sam.compliance import (
    ComplianceRegistry,
    ComplianceRunner,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceCategory,
    EvidenceType,
    Severity,
    ComplianceEvidence,
)
from sam.compliance.exceptions.compliance_errors import DuplicateCheckError


def _make_check(check_id, execution_fn=None, severity=None, evidence_type=None):
    return ComplianceCheck(
        check_id=check_id,
        level=ComplianceLevel.L0_STRUCTURAL,
        category=ComplianceCategory.RUNTIME_UNITS,
        description="Test check %s" % check_id,
        evidence_type=evidence_type or EvidenceType.FILE_EXISTS,
        severity=severity or Severity.MAJOR,
        baseline_ref="TEST_REF",
        execution_fn=execution_fn,
    )


class TestRunnerSingleExecution:
    """Running individual checks."""

    def test_run_executable_check_passing(self):
        reg = ComplianceRegistry()
        check = _make_check("T01", execution_fn=lambda: True)
        reg.register(check)

        runner = ComplianceRunner(reg)
        evidence = runner.run_check(check)

        assert evidence.check_id == "T01"
        assert evidence.is_passed()
        assert evidence.evidence_type == EvidenceType.FILE_EXISTS

    def test_run_executable_check_failing(self):
        reg = ComplianceRegistry()
        check = _make_check("T01", execution_fn=lambda: False)
        reg.register(check)

        runner = ComplianceRunner(reg)
        evidence = runner.run_check(check)

        assert evidence.check_id == "T01"
        assert evidence.is_failed()

    def test_run_placeholder_check(self):
        """Check without execution_fn produces COLLECTED evidence."""
        reg = ComplianceRegistry()
        check = _make_check("T01", execution_fn=None)
        reg.register(check)

        runner = ComplianceRunner(reg)
        evidence = runner.run_check(check)

        assert not evidence.is_passed()
        assert not evidence.is_failed()
        assert evidence.status == "COLLECTED"

    def test_run_check_raises_exception(self):
        """When execution_fn raises, it should produce FAILED evidence."""
        def raise_err():
            raise RuntimeError("simulated failure")

        reg = ComplianceRegistry()
        check = _make_check("T01", execution_fn=raise_err)
        reg.register(check)

        runner = ComplianceRunner(reg)
        evidence = runner.run_check(check)

        assert evidence.is_failed()
        assert "simulated failure" in evidence.details


class TestRunnerBatchExecution:
    """Running all checks."""

    def test_run_all_collects_all(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        reg.register(_make_check("T02", execution_fn=lambda: False))
        reg.register(_make_check("T03", execution_fn=None))

        runner = ComplianceRunner(reg)
        evidence = runner.run_all()

        assert len(evidence) == 3
        assert len(runner.evidence) == 3

    def test_run_all_deterministic(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("Z99", execution_fn=lambda: True))
        reg.register(_make_check("A01", execution_fn=lambda: True))
        reg.register(_make_check("M50", execution_fn=lambda: True))

        runner = ComplianceRunner(reg)
        evidence = runner.run_all()
        ids = [e.check_id for e in evidence]
        assert ids == ["A01", "M50", "Z99"]

    def test_run_by_level(self):
        reg = ComplianceRegistry()
        reg.register(ComplianceCheck(
            check_id="L0-01", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="L0 check", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.MAJOR, baseline_ref="TEST", execution_fn=lambda: True,
        ))
        reg.register(ComplianceCheck(
            check_id="L1-01", level=ComplianceLevel.L1_SPECIFICATION,
            category=ComplianceCategory.SPECIFICATION,
            description="L1 check", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL, baseline_ref="TEST", execution_fn=lambda: True,
        ))

        runner = ComplianceRunner(reg)
        l0_evidence = runner.run_by_level(ComplianceLevel.L0_STRUCTURAL)
        assert len(l0_evidence) == 1
        assert l0_evidence[0].check_id == "L0-01"

    def test_run_by_category(self):
        reg = ComplianceRegistry()
        reg.register(ComplianceCheck(
            check_id="C1", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.ADR,
            description="ADR check", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL, baseline_ref="TEST", execution_fn=lambda: True,
        ))
        reg.register(ComplianceCheck(
            check_id="C2", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.FOUNDATION,
            description="Foundation check", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL, baseline_ref="TEST", execution_fn=lambda: True,
        ))

        runner = ComplianceRunner(reg)
        adr_evidence = runner.run_by_category(ComplianceCategory.ADR)
        assert len(adr_evidence) == 1
        assert adr_evidence[0].check_id == "C1"


class TestRunnerAnalysis:
    """Evidence analysis produces findings."""

    def test_analyze_passing_produces_conformity(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        runner = ComplianceRunner(reg)
        runner.run_all()

        findings = runner.analyze()
        assert len(findings) == 1
        assert findings[0].is_conforming()

    def test_analyze_failing_produces_deviation(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: False))
        runner = ComplianceRunner(reg)
        runner.run_all()

        findings = runner.analyze()
        assert len(findings) == 1
        assert findings[0].is_deviating()

    def test_analyze_placeholder_produces_inconclusive(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=None))
        runner = ComplianceRunner(reg)
        runner.run_all()

        findings = runner.analyze()
        assert len(findings) == 1
        # INCONCLUSIVE check = not deviating = CONFORMITY severity
        # The classification is INCONCLUSIVE but severity is INFO
        assert findings[0].classification.value == "INCONCLUSIVE"

    def test_analyze_findings_sorted(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("Z02", execution_fn=lambda: False))
        reg.register(_make_check("A01", execution_fn=lambda: False))
        runner = ComplianceRunner(reg)
        runner.run_all()

        findings = runner.analyze()
        ids = [f.check_id for f in findings]
        assert ids == ["A01", "Z02"]


class TestRunnerClearEvidence:
    """Clearing evidence."""

    def test_clear_clears_all(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        runner = ComplianceRunner(reg)
        runner.run_all()
        assert len(runner.evidence) == 1

        runner.clear_evidence()
        assert len(runner.evidence) == 0
        assert len(runner.findings) == 0
