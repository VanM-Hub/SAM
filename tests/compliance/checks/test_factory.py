"""Test CheckFactory — config-driven construction of compliance checks."""

from __future__ import annotations

import pytest

from sam.compliance.checks.factory import CheckFactory, CheckFactoryError
from sam.compliance.checks.base import BaseComplianceCheck, CompositeComplianceCheck, CheckContext, CheckResult
from sam.compliance.models.level import ComplianceLevel
from sam.compliance.models.category import ComplianceCategory
from sam.compliance.models.severity import Severity
from sam.compliance.models.evidence_type import EvidenceType


class TestFactoryBasic:
    """Basic factory operations."""

    def test_create_file_exists_check(self):
        cfg = {
            "type": "FileExistsCheck",
            "check_id": "F-001",
            "level": "L0",
            "category": "Foundation",
            "description": "Check main init",
            "evidence_type": "FILE_EXISTS",
            "severity": "CRITICAL",
            "path": "src/__init__.py",
        }
        check = CheckFactory.create(cfg)
        assert check.check_id == "F-001"
        assert check.level == ComplianceLevel.L0_STRUCTURAL
        assert isinstance(check, BaseComplianceCheck)

    def test_create_all_types(self):
        types_to_test = [
            ("FileExistsCheck", {"path": "src/__init__.py"}),
            ("FileAbsentCheck", {"path": "nonexistent.py"}),
            ("SourceContainsCheck", {"file_pattern": "*.py", "search_pattern": "def"}),
            ("SourceAbsentCheck", {"file_pattern": "*.py", "forbidden_pattern": "TODO"}),
            ("ImportLegalCheck", {"file_pattern": "*.py", "allowed_imports": ["os", "sys"]}),
            ("ImportIllegalCheck", {"file_pattern": "*.py", "forbidden_imports": ["forbidden"]}),
            ("LifecycleCheck", {"transitions": {"A": ["B"], "B": ["C"]}}),
            ("TraceabilityCheck", {"file_pattern": "*.py"}),
            ("TestResultsCheck", {"test_pattern": "tests/**/test_*.py"}),
        ]
        for type_name, extra in types_to_test:
            cfg = {
                "type": type_name,
                "check_id": "T-%s" % type_name[:3],
                "level": "L0",
                "category": "Foundation",
                "description": "Test %s" % type_name,
                "evidence_type": "FILE_EXISTS",
                "severity": "CRITICAL",
                **extra,
            }
            check = CheckFactory.create(cfg)
            assert check.check_id == "T-%s" % type_name[:3], type_name

    def test_missing_type_raises(self):
        with pytest.raises(CheckFactoryError, match="'type'"):
            CheckFactory.create({"check_id": "X"})

    def test_missing_check_id_raises(self):
        with pytest.raises(CheckFactoryError, match="'check_id'"):
            CheckFactory.create({"type": "FileExistsCheck"})

    def test_unknown_type_raises(self):
        with pytest.raises(CheckFactoryError, match="Unknown"):
            CheckFactory.create({"type": "DoesNotExist", "check_id": "X"})

    def test_registered_types(self):
        types = CheckFactory.registered_types()
        assert "FileExistsCheck" in types
        assert "LifecycleCheck" in types
        assert "CompositeComplianceCheck" not in types  # handled specially
        assert len(types) == 9


class TestFactoryComposite:
    """Factory can build composite checks."""

    def test_create_composite_all(self):
        cfg = {
            "type": "CompositeComplianceCheck",
            "check_id": "COMP-ALL",
            "level": "L2",
            "category": "ADR",
            "description": "Composite AND",
            "evidence_type": "FILE_EXISTS",
            "severity": "CRITICAL",
            "mode": "ALL",
            "checks": [
                {"type": "FileExistsCheck", "check_id": "SUB-1", "path": "src/__init__.py",
                 "level": "L0", "category": "Foundation", "description": "A",
                 "evidence_type": "FILE_EXISTS", "severity": "CRITICAL"},
                {"type": "FileExistsCheck", "check_id": "SUB-2", "path": "src/__init__.py",
                 "level": "L0", "category": "Foundation", "description": "B",
                 "evidence_type": "FILE_EXISTS", "severity": "CRITICAL"},
            ],
        }
        check = CheckFactory.create(cfg)
        assert isinstance(check, CompositeComplianceCheck)
        assert check.mode.value == "ALL"
        assert len(check.checks) == 2

    def test_create_composite_any(self):
        cfg = {
            "type": "CompositeComplianceCheck",
            "check_id": "COMP-ANY",
            "level": "L2",
            "category": "ADR",
            "description": "Composite OR",
            "evidence_type": "FILE_EXISTS",
            "severity": "CRITICAL",
            "mode": "ANY",
            "checks": [
                {"type": "FileExistsCheck", "check_id": "SUB-A", "path": "nonexistent.py",
                 "level": "L0", "category": "Foundation", "description": "A",
                 "evidence_type": "FILE_EXISTS", "severity": "CRITICAL"},
                {"type": "FileExistsCheck", "check_id": "SUB-B", "path": "pyproject.toml",
                 "level": "L0", "category": "Foundation", "description": "B",
                 "evidence_type": "FILE_EXISTS", "severity": "CRITICAL"},
            ],
        }
        check = CheckFactory.create(cfg)
        assert check.mode.value == "ANY"
        # Should pass because at least one file exists (pyproject.toml)
        result = check.execute(CheckContext(target_path="."))
        assert result.passed

    def test_create_all(self):
        configs = [
            {"type": "FileExistsCheck", "check_id": "ALL-1", "path": "src/__init__.py",
             "level": "L0", "category": "Foundation", "description": "1",
             "evidence_type": "FILE_EXISTS", "severity": "CRITICAL"},
            {"type": "FileExistsCheck", "check_id": "ALL-2", "path": "src/__init__.py",
             "level": "L0", "category": "Foundation", "description": "2",
             "evidence_type": "FILE_EXISTS", "severity": "CRITICAL"},
        ]
        checks = CheckFactory.create_all(configs)
        assert len(checks) == 2
        assert checks[0].check_id == "ALL-1"
        assert checks[1].check_id == "ALL-2"


class TestFactoryDefaults:
    """Factory applies sensible defaults."""

    def test_default_level(self):
        cfg = {
            "type": "FileExistsCheck",
            "check_id": "DEF-L",
            "path": "src/__init__.py",
        }
        check = CheckFactory.create(cfg)
        assert check.level == ComplianceLevel.L0_STRUCTURAL

    def test_default_category(self):
        cfg = {
            "type": "FileExistsCheck",
            "check_id": "DEF-C",
            "path": "src/__init__.py",
        }
        check = CheckFactory.create(cfg)
        assert check.category == ComplianceCategory.FOUNDATION

    def test_default_severity(self):
        cfg = {
            "type": "FileExistsCheck",
            "check_id": "DEF-S",
            "path": "src/__init__.py",
        }
        check = CheckFactory.create(cfg)
        assert check.severity == Severity.INFO

    def test_default_evidence_type(self):
        cfg = {
            "type": "FileExistsCheck",
            "check_id": "DEF-E",
            "path": "src/__init__.py",
        }
        check = CheckFactory.create(cfg)
        assert check.evidence_type == EvidenceType.FILE_EXISTS


class TestFactoryTypeRegistry:
    """Type registry CRUD operations."""

    def test_register_custom_type(self):
        CheckFactory.clear_types()
        try:
            from sam.compliance.checks.filesystem.file_exists import FileExistsCheck
            CheckFactory.register_type("CustomExists", FileExistsCheck)
            assert "CustomExists" in CheckFactory.registered_types()

            check = CheckFactory.create({
                "type": "CustomExists",
                "check_id": "CUSTOM-1",
                "path": "src/__init__.py",
            })
            assert check.check_id == "CUSTOM-1"
        finally:
            # Re-register all types
            from sam.compliance.checks import _auto_register_types
            _auto_register_types()

    def test_duplicate_type_raises(self):
        with pytest.raises(CheckFactoryError, match="already registered"):
            from sam.compliance.checks.filesystem.file_exists import FileExistsCheck
            CheckFactory.register_type("FileExistsCheck", FileExistsCheck)

    def test_unregister_type(self):
        CheckFactory.clear_types()
        try:
            from sam.compliance.checks.filesystem.file_exists import FileExistsCheck
            CheckFactory.register_type("TestRemove", FileExistsCheck)
            assert "TestRemove" in CheckFactory.registered_types()
            CheckFactory.unregister_type("TestRemove")
            assert "TestRemove" not in CheckFactory.registered_types()
        finally:
            from sam.compliance.checks import _auto_register_types
            _auto_register_types()
