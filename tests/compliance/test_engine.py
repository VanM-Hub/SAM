"""Tests for ComplianceEngine."""

import pytest
from sam.compliance import (
    ComplianceRegistry,
    ComplianceEngine,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceCategory,
    EvidenceType,
    Severity,
    ComplianceEvidence,
    VerdictGrade,
)
from sam.compliance.exceptions.compliance_errors import SessionImmutableError


def _make_check(check_id, level=ComplianceLevel.L0_STRUCTURAL,
                execution_fn=None, severity=None):
    return ComplianceCheck(
        check_id=check_id,
        level=level,
        category=ComplianceCategory.RUNTIME_UNITS,
        description="Test check %s" % check_id,
        evidence_type=EvidenceType.FILE_EXISTS,
        severity=severity or Severity.MAJOR,
        baseline_ref="TEST_REF",
        execution_fn=execution_fn,
    )


class TestEngineConstruction:
    """Engine construction and basic properties."""

    def test_construct_with_valid_registry(self):
        reg = ComplianceRegistry()
        engine = ComplianceEngine(reg)
        assert engine.registry is reg

    def test_construct_with_invalid_registry_raises(self):
        with pytest.raises(TypeError):
            ComplianceEngine("not-a-registry")

    def test_initial_state_is_initiated(self):
        engine = ComplianceEngine(ComplianceRegistry())
        assert engine.state.name == "INITIATED"


class TestEngineSession:
    """Engine session execution."""

    def test_run_session_empty_registry(self):
        reg = ComplianceRegistry()
        engine = ComplianceEngine(reg)
        report = engine.run_session("target/path", "abc123")
        assert report.session_id != ""
        assert report.runtime_identity == "target/path"
        assert report.baseline_ref == "abc123"
        assert report.verdict.grade == VerdictGrade.A_CERTIFIED
        assert report.total_checks == 0

    def test_run_session_with_passing_checks(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        reg.register(_make_check("T02", execution_fn=lambda: True))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "def456")

        assert report.total_checks == 2
        assert report.total_passed == 2
        assert report.total_failed == 0
        assert report.verdict.grade == VerdictGrade.A_CERTIFIED
        assert len(report.findings) == 2

    def test_run_session_with_failing_check(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", severity=Severity.CRITICAL,
                                 execution_fn=lambda: False))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "ghi789")

        assert report.total_checks == 1
        assert report.total_passed == 0
        assert report.total_failed == 1
        assert report.verdict.grade == VerdictGrade.D_NOT_COMPLIANT

    def test_run_session_with_placeholder_checks(self):
        """Placeholder checks (no execution_fn) should be INCONCLUSIVE."""
        reg = ComplianceRegistry()
        reg.register(_make_check("T01"))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "abc")

        # Placeholder checks run but produce COLLECTED evidence
        assert report.total_checks == 1
        assert report.total_skipped == 1
        # No execution function → INCONCLUSIVE finding (not deviating)
        assert report.verdict.grade == VerdictGrade.A_CERTIFIED

    def test_run_session_terminal_raises(self):
        """Cannot run session again without reset."""
        reg = ComplianceRegistry()
        engine = ComplianceEngine(reg)
        engine.run_session("target", "abc")
        with pytest.raises(SessionImmutableError):
            engine.run_session("target2", "def")


class TestEngineVerdict:
    """Verdict computation."""

    def test_verdict_a_no_findings(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "abc")
        assert report.verdict.grade == VerdictGrade.A_CERTIFIED

    def test_verdict_d_critical(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", severity=Severity.CRITICAL,
                                 execution_fn=lambda: False))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "abc")
        assert report.verdict.grade == VerdictGrade.D_NOT_COMPLIANT
        assert report.verdict.critical_count == 1

    def test_verdict_c_major(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", severity=Severity.MAJOR,
                                 execution_fn=lambda: False))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "abc")
        assert report.verdict.grade == VerdictGrade.C_MAJOR_FINDING
        assert report.verdict.major_count == 1

    def test_verdict_b_minor_many(self):
        reg = ComplianceRegistry()
        for i in range(4):
            reg.register(_make_check("T%02d" % i, severity=Severity.MINOR,
                                     execution_fn=lambda: False))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "abc")
        assert report.verdict.grade == VerdictGrade.B_MINOR_FINDING
        assert report.verdict.minor_count == 4

    def test_verdict_a_minor_few(self):
        reg = ComplianceRegistry()
        for i in range(3):
            reg.register(_make_check("T%02d" % i, severity=Severity.MINOR,
                                     execution_fn=lambda: False))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "abc")
        # ≤3 MINOR → A
        assert report.verdict.grade == VerdictGrade.A_CERTIFIED


class TestEngineIdentity:
    """Session identity tracking."""

    def test_identity_after_session(self):
        reg = ComplianceRegistry()
        engine = ComplianceEngine(reg)
        report = engine.run_session("my-runtime", "baseline-abc")

        identity = engine.identity
        assert identity is not None
        assert identity.session_id == report.session_id
        assert identity.target_runtime == "my-runtime"
        assert identity.baseline_commit == "baseline-abc"
        assert identity.verdict == report.verdict.grade
        assert identity.is_complete()
        assert identity.evidence_count == report.total_evidence
        assert identity.finding_count == report.total_findings

    def test_identity_none_before_session(self):
        engine = ComplianceEngine(ComplianceRegistry())
        assert engine.identity is None


class TestEngineReset:
    """Engine reset behavior."""

    def test_reset_after_session(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        engine = ComplianceEngine(reg)

        engine.run_session("target1", "def456")
        engine.reset()

        # After reset, should be able to run a new session
        assert not engine.is_terminal()
        report2 = engine.run_session("target2", "def456")
        assert report2.runtime_identity == "target2"


class TestEngineEvidence:
    """Evidence collection behavior."""

    def test_evidence_collected(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("T01", execution_fn=lambda: True))
        reg.register(_make_check("T02", execution_fn=lambda: False))
        engine = ComplianceEngine(reg)
        report = engine.run_session("target", "abc")

        assert report.total_evidence == 2
        assert report.total_passed == 1
        assert report.total_failed == 1


class TestEngineDeterminism:
    """Engine must be deterministic."""

    def test_same_input_same_verdict(self):
        for _ in range(3):
            reg = ComplianceRegistry()
            reg.register(_make_check("T01", execution_fn=lambda: True))
            reg.register(_make_check("T02", execution_fn=lambda: True))
            engine = ComplianceEngine(reg)
            report = engine.run_session("same-target", "same-baseline")
            assert report.verdict.grade == VerdictGrade.A_CERTIFIED
            assert report.total_passed == 2

    def test_same_failing_input_same_verdict(self):
        for _ in range(3):
            reg = ComplianceRegistry()
            reg.register(_make_check("T01", severity=Severity.CRITICAL,
                                     execution_fn=lambda: False))
            engine = ComplianceEngine(reg)
            report = engine.run_session("target", "baseline")
            assert report.verdict.grade == VerdictGrade.D_NOT_COMPLIANT
