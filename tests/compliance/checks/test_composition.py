"""Test CompositeComplianceCheck — combining multiple checks."""

from __future__ import annotations

import pytest

from sam.compliance.checks.base import (
    BaseComplianceCheck,
    CheckContext,
    CheckResult,
    CompositeComplianceCheck,
    CompositeMode,
)
from sam.compliance.models.level import ComplianceLevel
from sam.compliance.models.category import ComplianceCategory
from sam.compliance.models.severity import Severity
from sam.compliance.models.evidence_type import EvidenceType


class _PassCheck(BaseComplianceCheck):
    def execute(self, context: CheckContext) -> CheckResult:
        return CheckResult.success(details="pass")


class _FailCheck(BaseComplianceCheck):
    def execute(self, context: CheckContext) -> CheckResult:
        return CheckResult.failure(details="fail")


def _make_pass(id_: str) -> _PassCheck:
    return _PassCheck(
        check_id=id_, level=ComplianceLevel.L0_STRUCTURAL,
        category=ComplianceCategory.RUNTIME_UNITS, description=id_,
        evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
    )


def _make_fail(id_: str) -> _FailCheck:
    return _FailCheck(
        check_id=id_, level=ComplianceLevel.L0_STRUCTURAL,
        category=ComplianceCategory.RUNTIME_UNITS, description=id_,
        evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
    )


class TestCompositeAll:
    """ALL mode (AND) — all sub-checks must pass."""

    def test_all_pass_pass(self):
        c = CompositeComplianceCheck(
            checks=[_make_pass("A"), _make_pass("B")],
            mode=CompositeMode.ALL,
            check_id="COMP", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="All pass",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert result.passed

    def test_one_fail_fails_all(self):
        c = CompositeComplianceCheck(
            checks=[_make_pass("A"), _make_fail("B")],
            mode=CompositeMode.ALL,
            check_id="COMP", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="One fail",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert not result.passed

    def test_all_fail_fails(self):
        c = CompositeComplianceCheck(
            checks=[_make_fail("A"), _make_fail("B")],
            mode=CompositeMode.ALL,
            check_id="COMP", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="All fail",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert not result.passed


class TestCompositeAny:
    """ANY mode (OR) — at least one sub-check must pass."""

    def test_any_pass_pass(self):
        c = CompositeComplianceCheck(
            checks=[_make_pass("A"), _make_pass("B")],
            mode=CompositeMode.ANY,
            check_id="COMP", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Any pass",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert result.passed

    def test_one_pass_passes_any(self):
        c = CompositeComplianceCheck(
            checks=[_make_pass("A"), _make_fail("B")],
            mode=CompositeMode.ANY,
            check_id="COMP", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="One pass",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert result.passed

    def test_all_fail_fails_any(self):
        c = CompositeComplianceCheck(
            checks=[_make_fail("A"), _make_fail("B")],
            mode=CompositeMode.ANY,
            check_id="COMP", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="All fail",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert not result.passed


class TestCompositeEmpty:
    """Edge cases for empty sub-check lists."""

    def test_empty_all_passes(self):
        c = CompositeComplianceCheck(
            checks=[], mode=CompositeMode.ALL,
            check_id="EMPTY", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Empty AND", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert result.passed  # vacuous truth

    def test_empty_any_fails(self):
        c = CompositeComplianceCheck(
            checks=[], mode=CompositeMode.ANY,
            check_id="EMPTY", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Empty OR", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert not result.passed  # no sub-check passes


class TestCompositeProperties:
    """Metadata and structural properties."""

    def test_check_list_is_copy(self):
        sub = [_make_pass("A")]
        c = CompositeComplianceCheck(
            checks=sub, mode=CompositeMode.ALL,
            check_id="COMP", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Copy",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        assert c.checks == sub
        assert c.checks is not sub  # should be a copy

    def test_metadata_forwarded(self):
        c = CompositeComplianceCheck(
            checks=[_make_pass("A")],
            check_id="META", level=ComplianceLevel.L3_BEHAVIORAL,
            category=ComplianceCategory.TESTING, description="Meta test",
            evidence_type=EvidenceType.TEST_PASS, severity=Severity.MINOR,
            baseline_ref="P1-001", recommendation="Fix",
        )
        assert c.check_id == "META"
        assert c.level == ComplianceLevel.L3_BEHAVIORAL
        assert c.baseline_ref == "P1-001"

    def test_to_config(self):
        c = CompositeComplianceCheck(
            checks=[_make_pass("A"), _make_fail("B")],
            mode=CompositeMode.ANY,
            check_id="CFG", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Config",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        config = c.to_config()
        assert config["type"] == "CompositeComplianceCheck"
        assert config["mode"] == "ANY"
        assert len(config["checks"]) == 2


class TestCompositeNested:
    """Composites can contain other composites."""

    def test_nested_composite(self):
        inner = CompositeComplianceCheck(
            checks=[_make_pass("A"), _make_pass("B")],
            mode=CompositeMode.ALL,
            check_id="INNER", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Inner",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        outer = CompositeComplianceCheck(
            checks=[inner, _make_pass("C")],
            mode=CompositeMode.ALL,
            check_id="OUTER", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Outer",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        result = outer.execute(CheckContext(target_path="."))
        assert result.passed
        # inner emits evidence with sub_results
        assert "sub_results" in result.evidence
