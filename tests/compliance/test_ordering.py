"""Tests for evidence ordering in check execution."""

from sam.compliance import (
    ComplianceRegistry,
    ComplianceRunner,
    ComplianceCheck,
    ComplianceLevel,
    ComplianceCategory,
    EvidenceType,
    Severity,
)


def _make_check(check_id, execution_fn=None):
    return ComplianceCheck(
        check_id=check_id,
        level=ComplianceLevel.L0_STRUCTURAL,
        category=ComplianceCategory.RUNTIME_UNITS,
        description="Check %s" % check_id,
        evidence_type=EvidenceType.FILE_EXISTS,
        severity=Severity.MAJOR,
        baseline_ref="TEST",
        execution_fn=execution_fn,
    )


class TestExecutionOrder:
    """Checks must execute in deterministic sorted-by-ID order."""

    def test_order_is_sorted_by_id(self):
        reg = ComplianceRegistry()
        order = []
        reg.register(_make_check("C", execution_fn=lambda: order.append("C") or True))
        reg.register(_make_check("A", execution_fn=lambda: order.append("A") or True))
        reg.register(_make_check("B", execution_fn=lambda: order.append("B") or True))

        runner = ComplianceRunner(reg)
        runner.run_all()

        assert order == ["A", "B", "C"]

    def test_evidence_order_matches_check_order(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("Z99", execution_fn=lambda: True))
        reg.register(_make_check("A01", execution_fn=lambda: True))

        runner = ComplianceRunner(reg)
        evidence = runner.run_all()

        assert evidence[0].check_id == "A01"
        assert evidence[1].check_id == "Z99"

    def test_finding_order_matches_check_order(self):
        reg = ComplianceRegistry()
        reg.register(_make_check("Z02", execution_fn=lambda: False))
        reg.register(_make_check("A01", execution_fn=lambda: False))

        runner = ComplianceRunner(reg)
        runner.run_all()
        findings = runner.analyze()

        assert findings[0].check_id == "A01"
        assert findings[1].check_id == "Z02"

    def test_order_is_deterministic(self):
        for _ in range(5):
            reg = ComplianceRegistry()
            order = []
            reg.register(_make_check("D", execution_fn=lambda: order.append("D") or True))
            reg.register(_make_check("C", execution_fn=lambda: order.append("C") or True))
            reg.register(_make_check("B", execution_fn=lambda: order.append("B") or True))
            reg.register(_make_check("A", execution_fn=lambda: order.append("A") or True))

            runner = ComplianceRunner(reg)
            runner.run_all()

            assert order == ["A", "B", "C", "D"]


class TestFindingOrdering:
    """Findings must be deterministically ordered."""

    def test_findings_stable_between_runs(self):
        for _ in range(3):
            reg = ComplianceRegistry()
            reg.register(_make_check("Z99", execution_fn=lambda: True))
            reg.register(_make_check("M50", execution_fn=lambda: False))
            reg.register(_make_check("A01", execution_fn=lambda: True))

            runner = ComplianceRunner(reg)
            runner.run_all()
            findings = runner.analyze()

            ids = [f.check_id for f in findings]
            assert ids == ["A01", "M50", "Z99"]
