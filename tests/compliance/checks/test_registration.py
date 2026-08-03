"""Test CheckRegistration — registering framework checks into engine registry."""

from __future__ import annotations

import pytest

from sam.compliance.checks.base import BaseComplianceCheck, CheckContext, CheckResult
from sam.compliance.checks.registry import CheckRegistration
from sam.compliance.registry.check_registry import ComplianceRegistry
from sam.compliance.checks.factory import CheckFactory, CheckFactoryError
from sam.compliance.models.level import ComplianceLevel
from sam.compliance.models.category import ComplianceCategory
from sam.compliance.models.severity import Severity
from sam.compliance.models.evidence_type import EvidenceType
from sam.compliance.exceptions.compliance_errors import DuplicateCheckError


class _FakeCheck(BaseComplianceCheck):
    """Check that always passes."""

    def execute(self, context: CheckContext) -> CheckResult:
        return CheckResult.success(details="always ok")


class _FakeCheckFail(BaseComplianceCheck):
    """Check that always fails."""

    def execute(self, context: CheckContext) -> CheckResult:
        return CheckResult.failure(details="always fail")


def _make_check(check_id: str) -> _FakeCheck:
    return _FakeCheck(
        check_id=check_id,
        level=ComplianceLevel.L0_STRUCTURAL,
        category=ComplianceCategory.RUNTIME_UNITS,
        description="Test check",
        evidence_type=EvidenceType.FILE_EXISTS,
        severity=Severity.CRITICAL,
    )


class TestRegistrationBasic:
    """Tests for basic check registration."""

    def test_register_single(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)
        cr.register(_make_check("T-001"))
        assert "T-001" in reg.check_ids()
        assert reg.find("T-001") is not None

    def test_register_duplicate_raises(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)
        cr.register(_make_check("T-001"))
        with pytest.raises(DuplicateCheckError):
            cr.register(_make_check("T-001"))

    def test_register_all(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)
        checks = [_make_check("T-001"), _make_check("T-002"), _make_check("T-003")]
        count = cr.register_all(checks)
        assert count == 3
        assert reg.count() == 3

    def test_register_all_duplicate_raises(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)
        cr.register(_make_check("T-001"))
        with pytest.raises(DuplicateCheckError):
            cr.register_all([_make_check("T-001"), _make_check("T-002")])

    def test_registered_checks_are_executable(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)
        cr.register(_make_check("T-001"))
        check = reg.get("T-001")
        assert check.is_executable()
        result = check.execute()
        assert result is True  # _FakeCheck returns True

    def test_runtime_error_converts(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)

        class _ErrorCheck(BaseComplianceCheck):
            def execute(self, context):
                raise RuntimeError("BOOM")

        cr.register(_ErrorCheck(
            check_id="ERR-001",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Error test",
            evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        ))
        check = reg.get("ERR-001")
        assert check.is_executable()

        # Execute through the engine runner, which catches exceptions
        from sam.compliance.engine.runner import ComplianceRunner
        runner = ComplianceRunner(reg)
        ev = runner.run_check(check)
        assert ev.is_failed()
        assert "BOOM" in ev.details


class TestRegistrationMetadata:
    """Tests for metadata preserved through registration."""

    def test_level_preserved(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)
        check = _FakeCheck(
            check_id="T-001",
            level=ComplianceLevel.L3_BEHAVIORAL,
            category=ComplianceCategory.TESTING,
            description="Level test",
            evidence_type=EvidenceType.TEST_PASS,
            severity=Severity.MINOR,
        )
        cr.register(check)
        cc = reg.get("T-001")
        assert cc.level == ComplianceLevel.L3_BEHAVIORAL
        assert cc.category == ComplianceCategory.TESTING
        assert cc.severity == Severity.MINOR

    def test_baseline_ref_preserved(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)
        check = _FakeCheck(
            check_id="T-001", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Ref test",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
            baseline_ref="P1-001", recommendation="Fix it",
        )
        cr.register(check)
        cc = reg.get("T-001")
        assert cc.baseline_ref == "P1-001"
        assert cc.recommendation == "Fix it"


class TestRegistrationWithContext:
    """Tests for context-sensitive registration."""

    def test_context_passed_to_execution(self):
        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)

        ctx = CheckContext(target_path="/custom/path", options={"key": "value"})

        class _PathCheck(BaseComplianceCheck):
            def execute(self, context):
                return CheckResult(
                    passed=context.target_path == "/custom/path",
                    details=context.target_path,
                    evidence=context.options,
                )

        cr.register(_PathCheck(
            check_id="CTX-001", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Context test",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        ), context=ctx)
        check = reg.get("CTX-001")
        assert check.is_executable()
        assert check.execute() is True


class TestRegisterPlaceholderChecks:
    """Tests for 99 placeholder checks."""

    def test_register_all_99(self):
        from sam.compliance.checks import register_placeholder_checks
        reg = ComplianceRegistry()
        count = register_placeholder_checks(reg)
        assert count == 99
        assert reg.count() == 99

    def test_placeholders_not_executable(self):
        from sam.compliance.checks import register_placeholder_checks
        reg = ComplianceRegistry()
        register_placeholder_checks(reg)
        for cid in reg.check_ids():
            check = reg.get(cid)
            assert not check.is_executable(), f"{cid} should be placeholder"
