"""Validation tests for the Compliance Baseline (P1-007).

Validation detects: duplicate file id, duplicate logical id, missing
baseline, orphan document, checksum consistency.
"""

import pytest

from sam.compliance.baseline import (
    BaselineValidator, BaselineValidationResult,
    BaselineSnapshot, BaselineEntry,
)
from sam.compliance.baseline.validator import _sha256


def _mk(file_id="FID-001", logical_id="LID-1", doc_type="document",
        authority=None, rel="docs/x.md", trace=(), checksum=None):
    return BaselineEntry(
        file_id=file_id, logical_id=logical_id, document_type=doc_type,
        authority=authority, checksum=checksum or ("a" * 64),
        relative_path=rel, traceability=tuple(trace),
    )


class TestCleanSnapshot:
    def test_valid_true(self):
        """Source/test entries (not orphan-eligible) validate clean."""
        snap = BaselineSnapshot([
            _mk(file_id="A", logical_id="LID-A", doc_type="source", rel="a.py"),
            _mk(file_id="B", logical_id="LID-B", doc_type="source", rel="b.py"),
        ])
        res = BaselineValidator(snap).validate(check_disk=False)
        assert res.valid
        assert len(res.issues) == 0

    def test_bool(self):
        snap = BaselineSnapshot([_mk()])
        res = BaselineValidator(snap).validate(check_disk=False)
        assert bool(res)


class TestDuplicateFileId:
    def test_construction_rejects_duplicate(self):
        from sam.compliance.baseline import ManifestError
        with pytest.raises(ManifestError):
            BaselineSnapshot([_mk(file_id="A"), _mk(file_id="A")])


class TestDuplicateLogicalId:
    def test_duplicate_logical_detected(self):
        snap = BaselineSnapshot([
            _mk(file_id="A", logical_id="LID"),
            _mk(file_id="B", logical_id="LID"),
        ])
        res = BaselineValidator(snap).validate(check_disk=False)
        assert not res.valid
        assert "duplicate_logical_id" in res.error_categories
        assert len(res.issues_for("duplicate_logical_id")) == 1


class TestMissingBaseline:
    def test_missing_reference_detected(self):
        snap = BaselineSnapshot([
            _mk(file_id="A", trace=("ZOMBIE",)),
        ])
        res = BaselineValidator(snap).validate(check_disk=False)
        assert not res.valid
        assert "missing_baseline" in res.error_categories


class TestOrphanDocument:
    def test_orphan_document_detected(self):
        """Orphan is detected as an issue (warning category)."""
        snap = BaselineSnapshot([
            _mk(file_id="DOC", doc_type="document", trace=()),
        ])
        res = BaselineValidator(snap).validate(check_disk=False)
        assert len(res.issues_for("orphan_document")) == 1

    def test_orphan_document_flagged_in_categories(self):
        snap = BaselineSnapshot([
            _mk(file_id="DOC", doc_type="document", trace=()),
        ])
        res = BaselineValidator(snap).validate(check_disk=False)
        cats = {i.category for i in res.issues}
        assert "orphan_document" in cats

    def test_referenced_document_not_orphan(self):
        snap = BaselineSnapshot([
            _mk(file_id="DOC", doc_type="document", trace=()),
            _mk(file_id="SRC", doc_type="source", trace=("DOC",)),
        ])
        res = BaselineValidator(snap).validate(check_disk=False)
        assert "orphan_document" not in res.error_categories


class TestChecksumConsistency:
    def test_checksum_mismatch_detected(self, tmp_path):
        f = tmp_path / "x.py"
        f.write_text("hello")
        snap = BaselineSnapshot([
            _mk(file_id="SRC", doc_type="source",
                rel="x.py", checksum="f" * 64),
        ])
        v = BaselineValidator(snap, loader=_FakeLoader(tmp_path))
        res = v.validate(check_disk=True)
        assert not res.valid
        assert "checksum_mismatch" in res.error_categories

    def test_checksum_match_ok(self, tmp_path):
        f = tmp_path / "x.py"
        f.write_text("hello")
        snap = BaselineSnapshot([
            _mk(file_id="SRC", doc_type="source",
                rel="x.py", checksum=_sha256(f)),
        ])
        v = BaselineValidator(snap, loader=_FakeLoader(tmp_path))
        res = v.validate(check_disk=True)
        assert res.valid


class _FakeLoader:
    """Minimal loader stub rooted at tmp_path for checksum re-read."""

    def __init__(self, root):
        self._root = root
