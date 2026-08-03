"""Test determinism — same check + same context = same result."""

from __future__ import annotations

from sam.compliance.checks.base import CheckContext
from sam.compliance.checks.filesystem import FileExistsCheck, FileAbsentCheck
from sam.compliance.checks.source import SourceContainsCheck, SourceAbsentCheck
from sam.compliance.checks.import_rules import ImportLegalCheck, ImportIllegalCheck
from sam.compliance.checks.lifecycle import LifecycleCheck
from sam.compliance.checks.traceability import TraceabilityCheck
from sam.compliance.checks.helpers import TestResultsCheck
from sam.compliance.checks.factory import CheckFactory
from sam.compliance.models.level import ComplianceLevel
from sam.compliance.models.category import ComplianceCategory
from sam.compliance.models.severity import Severity
from sam.compliance.models.evidence_type import EvidenceType
from sam.compliance.checks import register_placeholder_checks
from sam.compliance.registry.check_registry import ComplianceRegistry


RUNS = 5


class TestFileCheckDeterminism:
    def test_file_exists_deterministic(self):
        check = FileExistsCheck(
            check_id="FE", path="pyproject.toml",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Deterministic", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        ctx = CheckContext(target_path=".")
        results = [check.execute(ctx) for _ in range(RUNS)]
        assert all(r.passed == results[0].passed for r in results)
        assert all(r.details == results[0].details for r in results)

    def test_file_absent_deterministic(self):
        check = FileAbsentCheck(
            check_id="FA", path="nonexistent_abc.xyz",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Deterministic",
            evidence_type=EvidenceType.FILE_ABSENT,
            severity=Severity.CRITICAL,
        )
        ctx = CheckContext(target_path=".")
        results = [check.execute(ctx) for _ in range(RUNS)]
        assert all(r.passed == results[0].passed for r in results)


class TestLifecycleCheckDeterminism:
    def test_lifecycle_deterministic(self):
        check = LifecycleCheck(
            check_id="LC", transitions={"A": ["B"], "B": ["C"]},
            history=["A", "B", "C"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Deterministic",
            evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        ctx = CheckContext(target_path=".")
        results = [check.execute(ctx) for _ in range(RUNS)]
        assert all(r.passed == results[0].passed for r in results)
        assert all(r.details == results[0].details for r in results)


class TestImportCheckDeterminism:
    def test_import_illegal_deterministic(self):
        check = ImportIllegalCheck(
            check_id="II", file_pattern="*.py",
            forbidden_imports=["nonexistent_module"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Deterministic",
            evidence_type=EvidenceType.IMPORT_ILLEGAL,
            severity=Severity.CRITICAL,
        )
        ctx = CheckContext(target_path="src/sam/compliance/checks/")
        results = [check.execute(ctx) for _ in range(RUNS)]
        assert all(r.passed == results[0].passed for r in results)


class TestFactoryDeterminism:
    def test_factory_creates_deterministic_check(self):
        cfg = {
            "type": "LifecycleCheck",
            "check_id": "DET",
            "level": "L0",
            "category": "Foundation",
            "description": "Deterministic",
            "evidence_type": "LIFECYCLE_VALID",
            "severity": "CRITICAL",
            "transitions": {"A": ["B"], "B": ["C"]},
            "history": ["A", "B", "C"],
        }
        ctx = CheckContext(target_path=".")
        for _ in range(RUNS):
            check = CheckFactory.create(cfg)
            result = check.execute(ctx)
            assert result.passed

    def test_identical_configs_same_result(self):
        cfg = {
            "type": "FileExistsCheck",
            "check_id": "DET-FE",
            "path": "pyproject.toml",
            "level": "L0",
            "category": "Foundation",
            "description": "Deterministic",
            "evidence_type": "FILE_EXISTS",
            "severity": "CRITICAL",
        }
        ctx = CheckContext(target_path=".")
        results = []
        for _ in range(RUNS):
            check = CheckFactory.create(cfg)
            results.append(check.execute(ctx))
        assert all(r.passed == results[0].passed for r in results)


class TestPlaceholderDeterminism:
    def test_placeholder_registry_deterministic(self):
        """Same 99 placeholder checks registered each time."""
        results = []
        for _ in range(RUNS):
            reg = ComplianceRegistry()
            register_placeholder_checks(reg)
            results.append(sorted(reg.check_ids()))
        for ids in results[1:]:
            assert ids == results[0]
        assert len(results[0]) == 99
