"""BaselineValidator — validates the integrity of a baseline snapshot.

Per P1-007, validation detects:
    duplicate file id       — two entries share a file_id
    duplicate logical id    — two entries share a logical_id
    missing baseline        — a referenced file_id has no entry
    orphan document         — a document entry refers to nothing (no referrers)
    checksum consistency    — stored checksum differs from on-disk content

Validation produces a list of issues with categories; the snapshot is
considered valid only if there are no error-category issues.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from .entry import BaselineEntry
from .loader import BaselineLoader
from .snapshot import BaselineSnapshot


@dataclass
class BaselineValidationIssue:
    """A single validation issue."""

    category: str  # duplicate_file_id | duplicate_logical_id | missing_baseline | orphan_document | checksum_mismatch
    message: str

    def __repr__(self) -> str:
        return "BaselineValidationIssue(%s, %s)" % (self.category, self.message)


# Categories that make the snapshot invalid.
_ERROR_CATEGORIES = {
    "duplicate_file_id",
    "duplicate_logical_id",
    "missing_baseline",
    "checksum_mismatch",
}


class BaselineValidationResult:
    """Result of a validation pass."""

    def __init__(self, issues: List[BaselineValidationIssue]) -> None:
        self.issues = issues

    @property
    def valid(self) -> bool:
        """True if there are no error-category issues."""
        return not any(i.category in _ERROR_CATEGORIES for i in self.issues)

    @property
    def error_categories(self) -> Set[str]:
        return {i.category for i in self.issues if i.category in _ERROR_CATEGORIES}

    def issues_for(self, category: str) -> List[BaselineValidationIssue]:
        return [i for i in self.issues if i.category == category]

    def __bool__(self) -> bool:
        return self.valid


class BaselineValidator:
    """Validates a BaselineSnapshot."""

    def __init__(self, snapshot: BaselineSnapshot, loader: Optional[BaselineLoader] = None) -> None:
        """Build validator.

        Args:
            snapshot: The snapshot to validate.
            loader: Loader used to re-read files for checksum check.
                    Defaults to a loader rooted at the detected repo root.
        """
        self._snapshot = snapshot
        self._loader = loader or BaselineLoader()

    # -- Public API -----------------------------------------------------------

    def validate(self, check_disk: bool = True) -> BaselineValidationResult:
        """Run all validation checks."""
        issues: List[BaselineValidationIssue] = []
        issues.extend(self._check_duplicate_file_ids())
        issues.extend(self._check_duplicate_logical_ids())
        issues.extend(self._check_missing_baseline())
        issues.extend(self._check_orphan_documents())
        if check_disk:
            issues.extend(self._check_checksum_consistency())
        return BaselineValidationResult(issues)

    # -- Checks ---------------------------------------------------------------

    def _check_duplicate_file_ids(self) -> List[BaselineValidationIssue]:
        """Snapshot construction already rejects duplicate file_ids, but
        re-verify defensively for completeness."""
        issues: List[BaselineValidationIssue] = []
        seen: Dict[str, int] = {}
        for entry in self._snapshot.files():
            seen[entry.file_id] = seen.get(entry.file_id, 0) + 1
        for file_id, count in sorted(seen.items()):
            if count > 1:
                issues.append(BaselineValidationIssue(
                    "duplicate_file_id",
                    "file_id appears %d times: %s" % (count, file_id)))
        return issues

    def _check_duplicate_logical_ids(self) -> List[BaselineValidationIssue]:
        issues: List[BaselineValidationIssue] = []
        seen: Dict[str, List[str]] = {}
        for entry in self._snapshot.files():
            seen.setdefault(entry.logical_id, []).append(entry.file_id)
        for logical_id, file_ids in sorted(seen.items()):
            if len(file_ids) > 1:
                issues.append(BaselineValidationIssue(
                    "duplicate_logical_id",
                    "logical_id %s shared by %s" % (logical_id, file_ids)))
        return issues

    def _check_missing_baseline(self) -> List[BaselineValidationIssue]:
        """Find traceability references that point to no entry.

        A traceability ref is a file_id; if it does not resolve to an
        entry it is a missing baseline.
        """
        issues: List[BaselineValidationIssue] = []
        known_ids = {e.file_id for e in self._snapshot.files()}
        for entry in self._snapshot.files():
            for ref in entry.traceability:
                if ref not in known_ids:
                    issues.append(BaselineValidationIssue(
                        "missing_baseline",
                        "entry %s references missing file_id %s"
                        % (entry.file_id, ref)))
        return issues

    def _check_orphan_documents(self) -> List[BaselineValidationIssue]:
        """A document is orphan if nothing references its file_id and it
        references nothing (isolated). Isolation breaks traceability.

        Here 'orphan document' means: a document entry whose file_id is
        not referenced by any other entry (no incoming traceability).
        Documents are expected to be referenced by the manifest/catalog.
        """
        issues: List[BaselineValidationIssue] = []
        known_ids = {e.file_id for e in self._snapshot.files()}
        referenced: Set[str] = set()
        for entry in self._snapshot.files():
            for ref in entry.traceability:
                if ref in known_ids:
                    referenced.add(ref)
        for entry in self._snapshot.files():
            if entry.document_type != "document":
                continue
            if entry.file_id not in referenced:
                issues.append(BaselineValidationIssue(
                    "orphan_document",
                    "document %s is not referenced by any entry"
                    % entry.file_id))
        return issues

    def _check_checksum_consistency(self) -> List[BaselineValidationIssue]:
        """Re-read each file and compare its sha256 with the stored value."""
        issues: List[BaselineValidationIssue] = []
        for entry in self._snapshot.files():
            path = self._loader._root / entry.relative_path
            if not path.is_file():
                issues.append(BaselineValidationIssue(
                    "checksum_mismatch",
                    "missing on disk for %s (%s)" % (entry.file_id, entry.relative_path)))
                continue
            actual = _sha256(path)
            if actual != entry.checksum:
                issues.append(BaselineValidationIssue(
                    "checksum_mismatch",
                    "checksum mismatch for %s (%s)" % (entry.file_id, entry.relative_path)))
        return issues


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(str(path), "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()
