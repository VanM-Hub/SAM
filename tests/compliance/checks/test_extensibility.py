"""Test extensibility — framework can be extended without modification."""

from __future__ import annotations

from sam.compliance.checks.base import (
    BaseComplianceCheck,
    CheckContext,
    CheckResult,
)
from sam.compliance.checks.factory import CheckFactory, CheckFactoryError
from sam.compliance.checks.registry import CheckRegistration
from sam.compliance.registry.check_registry import ComplianceRegistry
from sam.compliance.models.level import ComplianceLevel
from sam.compliance.models.category import ComplianceCategory
from sam.compliance.models.severity import Severity
from sam.compliance.models.evidence_type import EvidenceType


class TestCustomCheck:
    """Framework can accept user-defined check types."""

    def test_custom_check_implements_contract(self):
        class MyCustomCheck(BaseComplianceCheck):
            def __init__(self, custom_field: str, **kwargs):
                super().__init__(**kwargs)
                self._custom_field = custom_field

            @property
            def custom_field(self) -> str:
                return self._custom_field

            def execute(self, context: CheckContext) -> CheckResult:
                return CheckResult.success(
                    details="custom field = %s" % self._custom_field,
                    evidence={"custom": self._custom_field},
                )

            def to_config(self) -> dict:
                cfg = super().to_config()
                cfg["custom_field"] = self._custom_field
                return cfg

        check = MyCustomCheck(
            check_id="CUSTOM", custom_field="hello",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Custom", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert result.passed
        assert result.evidence["custom"] == "hello"

    def test_custom_check_registerable(self):
        class MyCustomCheck(BaseComplianceCheck):
            def __init__(self, custom_field: str, **kwargs):
                super().__init__(**kwargs)
                self._custom_field = custom_field

            def execute(self, context: CheckContext) -> CheckResult:
                return CheckResult.success(details=self._custom_field)

        reg = ComplianceRegistry()
        cr = CheckRegistration(reg)
        cr.register(MyCustomCheck(
            check_id="CUSTOM-REG", custom_field="hello",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Custom", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        ))
        assert reg.find("CUSTOM-REG") is not None
        check = reg.get("CUSTOM-REG")
        assert check.is_executable()
        assert check.execute() is True

    def test_custom_check_in_factory(self):
        class MyCustomCheck(BaseComplianceCheck):
            def __init__(self, custom_field: str = "default", **kwargs):
                super().__init__(**kwargs)
                self._custom_field = custom_field

            def execute(self, context: CheckContext) -> CheckResult:
                return CheckResult.success(details=self._custom_field)

        # Register with factory
        CheckFactory.register_type("MyCustomCheck", MyCustomCheck)
        try:
            check = CheckFactory.create({
                "type": "MyCustomCheck",
                "check_id": "CUSTOM-F",
                "custom_field": "built_by_factory",
            })
            assert check.check_id == "CUSTOM-F"

            result = check.execute(CheckContext(target_path="."))
            assert result.passed
            assert "built_by_factory" in result.details
        finally:
            CheckFactory.unregister_type("MyCustomCheck")

    def test_unknown_custom_type_raises(self):
        import pytest
        from sam.compliance.checks.factory import CheckFactoryError
        with pytest.raises(CheckFactoryError):
            CheckFactory.create({"type": "UnregisteredType", "check_id": "X"})


class TestCheckStateless:
    """All framework checks are stateless."""

    def test_file_exists_is_stateless(self):
        from sam.compliance.checks.filesystem import FileExistsCheck
        check = FileExistsCheck(
            check_id="SL", path="pyproject.toml",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Stateless", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        ctx = CheckContext(target_path=".")
        r1 = check.execute(ctx)
        r2 = check.execute(ctx)
        assert r1.passed == r2.passed
        assert r1.details == r2.details

    def test_lifecycle_is_stateless(self):
        from sam.compliance.checks.lifecycle import LifecycleCheck
        check = LifecycleCheck(
            check_id="SL", transitions={"A": ["B", "C"]},
            history=["A", "B"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Stateless", evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        ctx = CheckContext(target_path=".")
        r1 = check.execute(ctx)
        r2 = check.execute(ctx)
        assert r1.passed == r2.passed

    def test_factory_built_check_is_stateless(self):
        cfg = {
            "type": "FileExistsCheck",
            "check_id": "SL-F",
            "path": "pyproject.toml",
            "level": "L0", "category": "Foundation",
            "description": "Stateless",
            "evidence_type": "FILE_EXISTS", "severity": "CRITICAL",
        }
        ctx = CheckContext(target_path=".")
        check1 = CheckFactory.create(cfg)
        check2 = CheckFactory.create(cfg)  # same config, new instance
        assert check1.execute(ctx).passed == check2.execute(ctx).passed


class TestCheckSelfDescribing:
    """All checks have complete metadata."""

    def test_all_checks_have_metadata(self):
        from sam.compliance.checks.filesystem import FileExistsCheck
        from sam.compliance.checks.lifecycle import LifecycleCheck
        from sam.compliance.checks.import_rules import ImportIllegalCheck
        from sam.compliance.checks.traceability import TraceabilityCheck
        from sam.compliance.checks.helpers import TestResultsCheck

        checks = [
            FileExistsCheck(check_id="SD", path=".",
                            level=ComplianceLevel.L0_STRUCTURAL,
                            category=ComplianceCategory.RUNTIME_UNITS,
                            description="A", evidence_type=EvidenceType.FILE_EXISTS,
                            severity=Severity.CRITICAL),
            LifecycleCheck(check_id="SD", transitions={"A": ["B"]},
                           level=ComplianceLevel.L0_STRUCTURAL,
                           category=ComplianceCategory.RUNTIME_UNITS,
                           description="B",
                           evidence_type=EvidenceType.LIFECYCLE_VALID,
                           severity=Severity.CRITICAL),
            ImportIllegalCheck(check_id="SD", file_pattern="*.py",
                               forbidden_imports=["bad"],
                               level=ComplianceLevel.L0_STRUCTURAL,
                               category=ComplianceCategory.RUNTIME_UNITS,
                               description="C",
                               evidence_type=EvidenceType.IMPORT_ILLEGAL,
                               severity=Severity.CRITICAL),
            TraceabilityCheck(check_id="SD", file_pattern="*.md",
                              level=ComplianceLevel.L0_STRUCTURAL,
                              category=ComplianceCategory.RUNTIME_UNITS,
                              description="D",
                              evidence_type=EvidenceType.TRACE_CHAIN,
                              severity=Severity.CRITICAL),
            TestResultsCheck(check_id="SD", test_pattern="*.py",
                            level=ComplianceLevel.L0_STRUCTURAL,
                            category=ComplianceCategory.RUNTIME_UNITS,
                            description="E",
                            evidence_type=EvidenceType.TEST_PASS,
                            severity=Severity.CRITICAL),
        ]

        for check in checks:
            assert len(check.check_id) > 0
            assert check.level is not None
            assert check.category is not None
            assert len(check.description) > 0
            assert check.severity is not None
            assert check.evidence_type is not None

    def test_all_checks_can_serialize(self):
        from sam.compliance.checks.filesystem import FileExistsCheck
        from sam.compliance.checks.lifecycle import LifecycleCheck
        from sam.compliance.checks.import_rules import ImportIllegalCheck
        from sam.compliance.checks.traceability import TraceabilityCheck
        from sam.compliance.checks.helpers import TestResultsCheck

        checks = [
            FileExistsCheck(check_id="SD", path=".",
                            level=ComplianceLevel.L0_STRUCTURAL,
                            category=ComplianceCategory.RUNTIME_UNITS,
                            description="A", evidence_type=EvidenceType.FILE_EXISTS,
                            severity=Severity.CRITICAL),
            LifecycleCheck(check_id="SD", transitions={"A": ["B"]},
                           level=ComplianceLevel.L0_STRUCTURAL,
                           category=ComplianceCategory.RUNTIME_UNITS,
                           description="B",
                           evidence_type=EvidenceType.LIFECYCLE_VALID,
                           severity=Severity.CRITICAL),
            ImportIllegalCheck(check_id="SD", file_pattern="*.py",
                               forbidden_imports=["bad"],
                               level=ComplianceLevel.L0_STRUCTURAL,
                               category=ComplianceCategory.RUNTIME_UNITS,
                               description="C",
                               evidence_type=EvidenceType.IMPORT_ILLEGAL,
                               severity=Severity.CRITICAL),
            TraceabilityCheck(check_id="SD", file_pattern="*.md",
                              level=ComplianceLevel.L0_STRUCTURAL,
                              category=ComplianceCategory.RUNTIME_UNITS,
                              description="D",
                              evidence_type=EvidenceType.TRACE_CHAIN,
                              severity=Severity.CRITICAL),
            TestResultsCheck(check_id="SD", test_pattern="*.py",
                            level=ComplianceLevel.L0_STRUCTURAL,
                            category=ComplianceCategory.RUNTIME_UNITS,
                            description="E",
                            evidence_type=EvidenceType.TEST_PASS,
                            severity=Severity.CRITICAL),
        ]

        for check in checks:
            cfg = check.to_config()
            assert "type" in cfg
            assert "check_id" in cfg
            assert "level" in cfg


class TestCheckComposable:
    """Framework checks can be composed."""

    def test_composite_with_real_checks(self):
        from sam.compliance.checks.base import CompositeComplianceCheck, CompositeMode
        from sam.compliance.checks.filesystem import FileExistsCheck

        c = CompositeComplianceCheck(
            checks=[
                FileExistsCheck(check_id="SUB-A", path="pyproject.toml",
                                level=ComplianceLevel.L0_STRUCTURAL,
                                category=ComplianceCategory.RUNTIME_UNITS,
                                description="A",
                                evidence_type=EvidenceType.FILE_EXISTS,
                                severity=Severity.CRITICAL),
                FileExistsCheck(check_id="SUB-B", path="README.md",
                                level=ComplianceLevel.L0_STRUCTURAL,
                                category=ComplianceCategory.RUNTIME_UNITS,
                                description="B",
                                evidence_type=EvidenceType.FILE_EXISTS,
                                severity=Severity.CRITICAL),
            ],
            mode=CompositeMode.ALL,
            check_id="COMP-REAL", level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS, description="Real composite",
            evidence_type=EvidenceType.FILE_EXISTS, severity=Severity.CRITICAL,
        )
        result = c.execute(CheckContext(target_path="."))
        assert result.passed

    def test_composite_from_factory_config(self):
        cfg = {
            "type": "CompositeComplianceCheck",
            "check_id": "COMP-CFG",
            "level": "L2", "category": "ADR",
            "description": "Config composite",
            "evidence_type": "FILE_EXISTS", "severity": "CRITICAL",
            "mode": "ALL",
            "checks": [
                {"type": "FileExistsCheck", "check_id": "S1",
                 "path": "pyproject.toml",
                 "level": "L0", "category": "Foundation",
                 "description": "S1", "evidence_type": "FILE_EXISTS",
                 "severity": "CRITICAL"},
                {"type": "FileExistsCheck", "check_id": "S2",
                 "path": "srctest.xyz",
                 "level": "L0", "category": "Foundation",
                 "description": "S2", "evidence_type": "FILE_EXISTS",
                 "severity": "CRITICAL"},
            ],
        }
        check = CheckFactory.create(cfg)
        result = check.execute(CheckContext(target_path="."))
        # S1 exists, S2 doesn't → ALL fails
        assert not result.passed
