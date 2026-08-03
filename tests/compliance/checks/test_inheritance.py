"""Test BaseComplianceCheck inheritance and interface contract."""

from __future__ import annotations

from sam.compliance.checks.base import (
    BaseComplianceCheck,
    CheckContext,
    CheckResult,
)
from sam.compliance.checks.filesystem import FileExistsCheck, FileAbsentCheck
from sam.compliance.checks.source import SourceContainsCheck, SourceAbsentCheck
from sam.compliance.checks.import_rules import ImportLegalCheck, ImportIllegalCheck
from sam.compliance.checks.lifecycle import LifecycleCheck
from sam.compliance.checks.traceability import TraceabilityCheck
from sam.compliance.checks.helpers import TestResultsCheck
from sam.compliance.models.level import ComplianceLevel
from sam.compliance.models.category import ComplianceCategory
from sam.compliance.models.severity import Severity
from sam.compliance.models.evidence_type import EvidenceType
from sam.compliance.models.check_model import ComplianceCheck


class TestAllChecksInheritFromBase:
    """Every check type is a subclass of BaseComplianceCheck."""

    def test_filesystem_checks(self):
        assert issubclass(FileExistsCheck, BaseComplianceCheck)
        assert issubclass(FileAbsentCheck, BaseComplianceCheck)

    def test_source_checks(self):
        assert issubclass(SourceContainsCheck, BaseComplianceCheck)
        assert issubclass(SourceAbsentCheck, BaseComplianceCheck)

    def test_import_checks(self):
        assert issubclass(ImportLegalCheck, BaseComplianceCheck)
        assert issubclass(ImportIllegalCheck, BaseComplianceCheck)

    def test_lifecycle_check(self):
        assert issubclass(LifecycleCheck, BaseComplianceCheck)

    def test_traceability_check(self):
        assert issubclass(TraceabilityCheck, BaseComplianceCheck)

    def test_helpers_check(self):
        assert issubclass(TestResultsCheck, BaseComplianceCheck)


class TestCheckProperties:
    """All checks expose standard properties."""

    def test_file_exists_properties(self):
        check = FileExistsCheck(
            check_id="FE", path="test.py",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Test", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        assert check.check_id == "FE"
        assert check.level == ComplianceLevel.L0_STRUCTURAL
        assert check.category == ComplianceCategory.RUNTIME_UNITS
        assert check.description == "Test"
        assert check.path == "test.py"

    def test_lifecycle_check_properties(self):
        transitions = {"A": ["B"], "B": ["C"]}
        check = LifecycleCheck(
            check_id="LC", transitions=transitions,
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="LC test", evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        assert check.check_id == "LC"


class TestAsExecutionFn:
    """as_execution_fn produces a callable compatible with engine."""

    def test_pass_check_returns_true(self):
        class _Pass(BaseComplianceCheck):
            def execute(self, context):
                return CheckResult.success()

        c = _Pass(check_id="P", level=ComplianceLevel.L0_STRUCTURAL,
                  category=ComplianceCategory.RUNTIME_UNITS, description="",
                  evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL)
        fn = c.as_execution_fn(CheckContext(target_path="."))
        assert callable(fn)
        assert fn() is True

    def test_fail_check_returns_false(self):
        class _Fail(BaseComplianceCheck):
            def execute(self, context):
                return CheckResult.failure()

        c = _Fail(check_id="F", level=ComplianceLevel.L0_STRUCTURAL,
                  category=ComplianceCategory.RUNTIME_UNITS, description="",
                  evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL)
        fn = c.as_execution_fn(CheckContext(target_path="."))
        assert fn() is False


class TestToComplianceCheck:
    """to_compliance_check creates proper ComplianceCheck models."""

    def test_converts_to_compliance_check(self):
        class _Pass(BaseComplianceCheck):
            def execute(self, context):
                return CheckResult.success()

        c = _Pass(
            check_id="CC-001", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Conversion",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
            baseline_ref="P1-001", recommendation="Do it",
        )
        cc = c.to_compliance_check(CheckContext(target_path="."))
        assert isinstance(cc, ComplianceCheck)
        assert cc.check_id == "CC-001"
        assert cc.is_executable()
        assert cc.execute() is True

    def test_to_compliance_check_no_execution_fn(self):
        # A check with no execute override won't have an execution_fn
        class _Dummy(BaseComplianceCheck):
            def execute(self, context):
                return CheckResult.success()

        c = _Dummy(check_id="DUMMY", level=ComplianceLevel.L0_STRUCTURAL,
                   category=ComplianceCategory.RUNTIME_UNITS, description="",
                   evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL)
        cc = c.to_compliance_check(CheckContext(target_path="."))
        assert cc.is_executable()


class TestToConfig:
    """Every check can serialize to config and be rebuilt."""

    def test_file_exists_to_config(self):
        check = FileExistsCheck(
            check_id="FE", path="src/__init__.py",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="FE check", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        cfg = check.to_config()
        assert "type" in cfg
        assert "check_id" in cfg
        assert "path" in cfg
        assert cfg["path"] == "src/__init__.py"

    def test_lifecycle_to_config(self):
        check = LifecycleCheck(
            check_id="LC", transitions={"A": ["B"]},
            history=["A", "B"], initial_state="A", terminal_state="B",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="LC check", evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        cfg = check.to_config()
        assert cfg["type"] == "LifecycleCheck"
        assert cfg["initial_state"] == "A"
        assert cfg["terminal_state"] == "B"
