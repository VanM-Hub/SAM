"""Tests for deterministic behavior of the compliance engine."""

from sam.compliance import (
    ComplianceRegistry,
    ComplianceEngine,
    ComplianceRunner,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceCategory,
    EvidenceType,
    Severity,
    ComplianceVerdict,
    VerdictGrade,
    SessionLifecycle,
    SessionState,
)


def _make_check(check_id, execution_fn=None, severity=None):
    return ComplianceCheck(
        check_id=check_id,
        level=ComplianceLevel.L0_STRUCTURAL,
        category=ComplianceCategory.RUNTIME_UNITS,
        description="Check %s" % check_id,
        evidence_type=EvidenceType.FILE_EXISTS,
        severity=severity or Severity.MAJOR,
        baseline_ref="TEST_REF",
        execution_fn=execution_fn,
    )


class TestEngineDeterminism:
    """ComplianceEngine must produce identical results for identical inputs."""

    def test_same_checks_same_verdict(self):
        for _ in range(5):
            reg = ComplianceRegistry()
            reg.register(_make_check("T01", execution_fn=lambda: True))
            reg.register(_make_check("T02", execution_fn=lambda: True))
            engine = ComplianceEngine(reg)
            report = engine.run_session("target", "baseline")
            assert report.verdict.grade == VerdictGrade.A_CERTIFIED
            assert report.total_passed == 2

    def test_same_failures_same_verdict(self):
        for _ in range(5):
            reg = ComplianceRegistry()
            reg.register(_make_check("T01", severity=Severity.CRITICAL,
                                     execution_fn=lambda: False))
            engine = ComplianceEngine(reg)
            report = engine.run_session("target", "baseline")
            assert report.verdict.grade == VerdictGrade.D_NOT_COMPLIANT
            assert report.verdict.critical_count == 1

    def test_mixed_checks_same_verdict(self):
        for _ in range(5):
            reg = ComplianceRegistry()
            reg.register(_make_check("T01", execution_fn=lambda: True))
            reg.register(_make_check("T02", execution_fn=lambda: False,
                                     severity=Severity.MAJOR))
            reg.register(_make_check("T03", execution_fn=lambda: True))
            engine = ComplianceEngine(reg)
            report = engine.run_session("target", "baseline")
            assert report.verdict.grade == VerdictGrade.C_MAJOR_FINDING
            assert report.verdict.major_count == 1
            assert report.total_passed == 2


class TestRunnerDeterminism:
    """ComplianceRunner must produce identical results for identical inputs."""

    def test_runner_deterministic(self):
        for _ in range(5):
            reg = ComplianceRegistry()
            reg.register(_make_check("A", execution_fn=lambda: True))
            reg.register(_make_check("B", execution_fn=lambda: True))
            reg.register(_make_check("C", execution_fn=lambda: True))

            runner = ComplianceRunner(reg)
            evidence = runner.run_all()
            findings = runner.analyze()

            assert len(evidence) == 3
            assert len(findings) == 3
            assert all(f.is_conforming() for f in findings)


class TestLifecycleDeterminism:
    """SessionLifecycle must be deterministic."""

    def test_transitions_deterministic(self):
        for _ in range(5):
            lc = SessionLifecycle()
            transitions = [
                SessionState.EVIDENCE_COLLECTION,
                SessionState.ANALYSIS,
                SessionState.PRELIMINARY_VERDICT,
                SessionState.FINAL_VERDICT,
                SessionState.ARCHIVED,
            ]
            for t in transitions:
                assert lc.can_transition_to(t)
                lc.transition_to(t)
            assert lc.state == SessionState.ARCHIVED


class TestRegistryDeterminism:
    """ComplianceRegistry must be deterministic."""

    def test_list_all_deterministic(self):
        for _ in range(5):
            reg = ComplianceRegistry()
            reg.register(_make_check("Z"))
            reg.register(_make_check("A"))
            reg.register(_make_check("M"))
            ids = [c.check_id for c in reg.list_all()]
            assert ids == ["A", "M", "Z"]

    def test_group_deterministic(self):
        for _ in range(5):
            reg = ComplianceRegistry()
            reg.register(_make_check("B"))
            reg.register(_make_check("A"))
            ids_L0 = [c.check_id for c in reg.list_by_level(ComplianceLevel.L0_STRUCTURAL)]
            assert ids_L0 == ["A", "B"]


class TestVerdictDeterminism:
    """Verdict computation must be deterministic."""

    def test_compute_deterministic(self):
        for _ in range(10):
            v = ComplianceVerdict.compute(0, 1, 3, 2)
            assert v.grade == VerdictGrade.C_MAJOR_FINDING
            assert v.critical_count == 0
            assert v.major_count == 1
            assert v.minor_count == 3

    def test_edge_case_deterministic(self):
        """Exactly 3 minor → A, exactly 4 → B — must be consistent."""
        for _ in range(10):
            v3 = ComplianceVerdict.compute(0, 0, 3)
            v4 = ComplianceVerdict.compute(0, 0, 4)
            assert v3.grade == VerdictGrade.A_CERTIFIED
            assert v4.grade == VerdictGrade.B_MINOR_FINDING
