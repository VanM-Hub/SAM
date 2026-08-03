"""Test execution of concrete check types with real filesystem."""

from __future__ import annotations

import os
import tempfile

from sam.compliance.checks.base import CheckContext
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


class TestFileExistsExecution:
    """FileExistsCheck execution tests."""

    def test_existing_file_passes(self):
        check = FileExistsCheck(
            check_id="FE", path="pyproject.toml",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Check pyproject", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert result.passed
        assert "exists" in result.details.lower()
        assert result.evidence["exists"] is True

    def test_nonexistent_file_fails(self):
        check = FileExistsCheck(
            check_id="FE", path="nonexistent_xyz.abc",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Missing file", evidence_type=EvidenceType.FILE_EXISTS,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert not result.passed
        assert result.evidence["exists"] is False


class TestFileAbsentExecution:
    """FileAbsentCheck execution tests."""

    def test_absent_file_passes(self):
        check = FileAbsentCheck(
            check_id="FA", path="nonexistent_xyz.abc",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="File must not exist",
            evidence_type=EvidenceType.FILE_ABSENT,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert result.passed

    def test_existing_file_fails(self):
        check = FileAbsentCheck(
            check_id="FA", path="pyproject.toml",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="File should not exist",
            evidence_type=EvidenceType.FILE_ABSENT,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert not result.passed
        assert result.evidence["exists"] is True


class TestSourceExecution:
    """Source check execution tests."""

    @staticmethod
    def _write_temp_file(dir_path, name, content):
        p = os.path.join(dir_path, name)
        with open(p, "w") as f:
            f.write(content)
        return p

    def test_source_contains_finds_match(self, tmp_path):
        self._write_temp_file(str(tmp_path), "test.py", "def hello():\n    return 42\n")
        check = SourceContainsCheck(
            check_id="SC", file_pattern="*.py", search_pattern=r"def hello",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Find def hello",
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert result.passed

    def test_source_contains_no_match_fails(self, tmp_path):
        self._write_temp_file(str(tmp_path), "test.py", "x = 1\n")
        check = SourceContainsCheck(
            check_id="SC", file_pattern="*.py", search_pattern=r"def hello",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Find def hello",
            evidence_type=EvidenceType.SOURCE_CONTAINS,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert not result.passed

    def test_source_absent_passes_when_no_match(self, tmp_path):
        self._write_temp_file(str(tmp_path), "test.py", "x = 1\n")
        check = SourceAbsentCheck(
            check_id="SA", file_pattern="*.py", forbidden_pattern=r"TODO",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="No TODO",
            evidence_type=EvidenceType.SOURCE_ABSENT,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert result.passed

    def test_source_absent_fails_when_found(self, tmp_path):
        self._write_temp_file(str(tmp_path), "test.py", "# TODO fix this\n")
        check = SourceAbsentCheck(
            check_id="SA", file_pattern="*.py", forbidden_pattern=r"TODO",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="No TODO allowed",
            evidence_type=EvidenceType.SOURCE_ABSENT,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert not result.passed


class TestImportExecution:
    """Import check execution tests."""

    @staticmethod
    def _write_temp_file(dir_path, name, content):
        p = os.path.join(dir_path, name)
        with open(p, "w") as f:
            f.write(content)
        return p

    def test_import_illegal_detects_forbidden(self, tmp_path):
        self._write_temp_file(str(tmp_path), "mod.py",
                              "import os\nimport sys\nimport forbidden_module\n")
        check = ImportIllegalCheck(
            check_id="II", file_pattern="*.py",
            forbidden_imports=["forbidden_module"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="No forbidden imports",
            evidence_type=EvidenceType.IMPORT_ILLEGAL,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert not result.passed

    def test_import_illegal_passes_when_clean(self, tmp_path):
        self._write_temp_file(str(tmp_path), "mod.py", "import os\nimport sys\n")
        check = ImportIllegalCheck(
            check_id="II", file_pattern="*.py",
            forbidden_imports=["forbidden_module"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="No forbidden imports",
            evidence_type=EvidenceType.IMPORT_ILLEGAL,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert result.passed

    def test_import_legal_detects_illegal(self, tmp_path):
        self._write_temp_file(str(tmp_path), "mod.py",
                              "import os\nimport unknown_lib\n")
        check = ImportLegalCheck(
            check_id="IL", file_pattern="*.py",
            allowed_imports=["os", "sys"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Only os/sys imports",
            evidence_type=EvidenceType.IMPORT_LEGAL,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert not result.passed

    def test_import_legal_passes_when_all_allowed(self, tmp_path):
        self._write_temp_file(str(tmp_path), "mod.py", "import os\nfrom sys import path\n")
        check = ImportLegalCheck(
            check_id="IL", file_pattern="*.py",
            allowed_imports=["os", "sys"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Only os/sys",
            evidence_type=EvidenceType.IMPORT_LEGAL,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert result.passed

    def test_import_legal_with_exclude(self, tmp_path):
        self._write_temp_file(str(tmp_path), "mod.py", "import unknown_lib\n")
        self._write_temp_file(str(tmp_path), "bad.py", "import bad_lib\n")
        check = ImportLegalCheck(
            check_id="IL", file_pattern="*.py",
            allowed_imports=["unknown_lib"],
            exclude_files=["bad.py"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Exclude bad.py",
            evidence_type=EvidenceType.IMPORT_LEGAL,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert result.passed


class TestLifecycleExecution:
    """LifecycleCheck execution tests."""

    def test_valid_transitions_passes(self):
        check = LifecycleCheck(
            check_id="LC", transitions={"A": ["B", "C"], "B": ["C"], "C": []},
            history=["A", "B", "C"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Valid lifecycle",
            evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert result.passed

    def test_invalid_transition_fails(self):
        check = LifecycleCheck(
            check_id="LC", transitions={"A": ["B"], "B": ["C"]},
            history=["A", "C"],  # A→C is invalid
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Invalid transition",
            evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert not result.passed
        assert len(result.evidence["errors"]) == 1

    def test_wrong_initial_state_fails(self):
        check = LifecycleCheck(
            check_id="LC", transitions={"A": ["B"], "B": ["C"]},
            history=["B", "C"], initial_state="A",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Wrong initial", evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert not result.passed

    def test_wrong_terminal_state_fails(self):
        check = LifecycleCheck(
            check_id="LC", transitions={"A": ["B"], "B": ["C"]},
            history=["A", "B"], terminal_state="C",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Wrong terminal", evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert not result.passed

    def test_empty_history_with_initial_fails(self):
        check = LifecycleCheck(
            check_id="LC", transitions={"A": ["B"]},
            history=[], initial_state="A",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Empty history", evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert not result.passed

    def test_empty_history_passes_when_no_state_checks(self):
        check = LifecycleCheck(
            check_id="LC", transitions={"A": ["B"]},
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Empty history ok",
            evidence_type=EvidenceType.LIFECYCLE_VALID,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert result.passed


class TestTraceabilityExecution:
    """TraceabilityCheck execution tests."""

    def test_with_refs_passes(self, tmp_path):
        import os
        p = os.path.join(str(tmp_path), "doc.md")
        with open(p, "w") as f:
            f.write("# Title\nRef: P1-001\nSee also: ADR-002\n")
        check = TraceabilityCheck(
            check_id="TR", file_pattern="*.md",
            required_refs=["P1-001"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Has refs", evidence_type=EvidenceType.TRACE_CHAIN,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert result.passed

    def test_missing_refs_fails(self, tmp_path):
        import os
        p = os.path.join(str(tmp_path), "doc.md")
        with open(p, "w") as f:
            f.write("# No refs here\n")
        check = TraceabilityCheck(
            check_id="TR", file_pattern="*.md",
            required_refs=["P1-001"],
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Has refs", evidence_type=EvidenceType.TRACE_CHAIN,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert not result.passed

    def test_no_files_passes(self):
        check = TraceabilityCheck(
            check_id="TR", file_pattern="nonexistent_*.xyz",
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="No files", evidence_type=EvidenceType.TRACE_CHAIN,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert result.passed


class TestTestResultExecution:
    """TestResultsCheck execution tests."""

    def test_test_files_found_passes(self):
        check = TestResultsCheck(
            check_id="TR", test_pattern="tests/compliance/**/test_*.py",
            min_count=1, check_content=True,
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Has tests", evidence_type=EvidenceType.TEST_PASS,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path="."))
        assert result.passed

    def test_min_count_fails(self, tmp_path):
        import os
        p = os.path.join(str(tmp_path), "test_one.py")
        with open(p, "w") as f:
            f.write("def test_stuff(): pass\n")
        check = TestResultsCheck(
            check_id="TR", test_pattern="*.py",
            min_count=5,
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Need 5 tests", evidence_type=EvidenceType.TEST_PASS,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert not result.passed

    def test_content_check_detects_no_test_fn(self, tmp_path):
        import os
        p = os.path.join(str(tmp_path), "test_no_fn.py")
        with open(p, "w") as f:
            f.write("x = 1\n")
        check = TestResultsCheck(
            check_id="TR", test_pattern="*.py",
            check_content=True,
            level=ComplianceLevel.L0_STRUCTURAL,
            category=ComplianceCategory.RUNTIME_UNITS,
            description="Need test fn", evidence_type=EvidenceType.TEST_PASS,
            severity=Severity.CRITICAL,
        )
        result = check.execute(CheckContext(target_path=str(tmp_path)))
        assert not result.passed
