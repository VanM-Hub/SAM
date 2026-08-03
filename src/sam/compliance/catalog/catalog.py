"""ComplianceCheckCatalog — canonical registry of all 99 P1-001 checks.

The catalog is the single source of truth for check metadata.
It is built once from _entries.py and provides query/filter methods.

Read-only after construction — catalog is immutable.
"""

from typing import Dict, List, Optional, Iterator

from .models import (
    CheckMetadata, CheckLevel, CheckCategory, CheckSeverity,
    EvidenceType, CheckAuthority, CheckerClass,
)
from ._entries import build_all_entries


class CatalogError(Exception):
    """Catalog-level error (e.g., duplicate ID, missing entry)."""
    pass


class ComplianceCheckCatalog:
    """Canonical registry of all 99 P1-001 compliance check metadata.

    Usage:
        catalog = ComplianceCheckCatalog()
        check = catalog.get("L1-C01")
        for ch in catalog.by_level(CheckLevel.L1_SPECIFICATION):
            print(ch.check_id)
    """

    def __init__(self):
        """Build the catalog from P1-001 _entries.py."""
        all_entries = build_all_entries()
        self._by_id: Dict[str, CheckMetadata] = {}
        self._by_level: Dict[CheckLevel, List[CheckMetadata]] = {
            l: [] for l in CheckLevel
        }
        self._by_category: Dict[CheckCategory, List[CheckMetadata]] = {
            c: [] for c in CheckCategory
        }
        self._by_authority: Dict[CheckAuthority, List[CheckMetadata]] = {
            a: [] for a in CheckAuthority
        }
        self._by_evidence: Dict[EvidenceType, List[CheckMetadata]] = {
            e: [] for e in EvidenceType
        }
        self._by_checker: Dict[CheckerClass, List[CheckMetadata]] = {
            c: [] for c in CheckerClass
        }

        seen: set = set()
        for entry in all_entries:
            if entry.check_id in seen:
                raise CatalogError("Duplicate check ID: %s" % entry.check_id)
            seen.add(entry.check_id)
            self._by_id[entry.check_id] = entry
            self._by_level[entry.level].append(entry)
            self._by_category[entry.category].append(entry)
            self._by_authority[entry.authority].append(entry)
            self._by_evidence[entry.evidence_type].append(entry)
            self._by_checker[entry.checker_class].append(entry)

        self._count = len(self._by_id)

    # -- Properties -----------------------------------------------------------

    @property
    def count(self) -> int:
        """Total check count (should be 99)."""
        return self._count

    @property
    def levels(self) -> List[CheckLevel]:
        """All levels represented in catalog."""
        return sorted(self._by_level.keys(), key=lambda l: l.value)

    @property
    def categories(self) -> List[CheckCategory]:
        """All categories represented in catalog."""
        return sorted(self._by_category.keys(), key=lambda c: c.value)

    @property
    def authorities(self) -> List[CheckAuthority]:
        """All authorities represented in catalog."""
        return sorted(self._by_authority.keys(), key=lambda a: a.value)

    @property
    def evidence_types(self) -> List[EvidenceType]:
        """All evidence types represented in catalog."""
        return sorted(self._by_evidence.keys(), key=lambda e: e.value)

    @property
    def checker_classes(self) -> List[CheckerClass]:
        """All checker classes represented in catalog."""
        return sorted(self._by_checker.keys(), key=lambda c: c.value)

    # -- Core queries ---------------------------------------------------------

    def get(self, check_id: str) -> Optional[CheckMetadata]:
        """Get a single check by ID. Returns None if not found."""
        return self._by_id.get(check_id)

    def list_all(self) -> List[CheckMetadata]:
        """List all checks, sorted by ID."""
        return sorted(self._by_id.values(), key=lambda c: c.check_id)

    def __iter__(self) -> Iterator[CheckMetadata]:
        return iter(self.list_all())

    def __len__(self) -> int:
        return self._count

    def __contains__(self, check_id: str) -> bool:
        return check_id in self._by_id

    def __getitem__(self, check_id: str) -> CheckMetadata:
        entry = self._by_id.get(check_id)
        if entry is None:
            raise KeyError("Check not found: %s" % check_id)
        return entry

    # -- Filter queries -------------------------------------------------------

    def by_level(self, level: CheckLevel) -> List[CheckMetadata]:
        """All checks at a given compliance level."""
        return sorted(self._by_level.get(level, []),
                      key=lambda c: c.check_id)

    def by_category(self, category: CheckCategory) -> List[CheckMetadata]:
        """All checks in a given category."""
        return sorted(self._by_category.get(category, []),
                      key=lambda c: c.check_id)

    def by_authority(self, authority: CheckAuthority) -> List[CheckMetadata]:
        """All checks authorized by a given authority."""
        return sorted(self._by_authority.get(authority, []),
                      key=lambda c: c.check_id)

    def by_evidence(self, evidence_type: EvidenceType) -> List[CheckMetadata]:
        """All checks requiring a given evidence type."""
        return sorted(self._by_evidence.get(evidence_type, []),
                      key=lambda c: c.check_id)

    def by_checker(self, checker_class: CheckerClass) -> List[CheckMetadata]:
        """All checks implemented by a given checker class."""
        return sorted(self._by_checker.get(checker_class, []),
                      key=lambda c: c.check_id)

    def by_tag(self, tag: str) -> List[CheckMetadata]:
        """All checks with a given tag."""
        return sorted(
            [c for c in self._by_id.values() if tag in c.tags],
            key=lambda c: c.check_id,
        )

    def by_source_document(self, document: str) -> List[CheckMetadata]:
        """All checks referencing a given source document."""
        return sorted(
            [c for c in self._by_id.values()
             if c.source_document == document],
            key=lambda c: c.check_id,
        )

    # -- Statistics -----------------------------------------------------------

    def level_distribution(self) -> Dict[str, int]:
        """Count of checks per level."""
        return {
            level.value: len(checks)
            for level, checks in self._by_level.items()
            if checks
        }

    def category_distribution(self) -> Dict[str, int]:
        """Count of checks per category."""
        return {
            cat.value: len(checks)
            for cat, checks in self._by_category.items()
            if checks
        }

    def authority_distribution(self) -> Dict[str, int]:
        """Count of checks per authority."""
        return {
            auth.value: len(checks)
            for auth, checks in self._by_authority.items()
            if checks
        }

    def evidence_distribution(self) -> Dict[str, int]:
        """Count of checks per evidence type."""
        return {
            ev.value: len(checks)
            for ev, checks in self._by_evidence.items()
            if checks
        }

    def checker_distribution(self) -> Dict[str, int]:
        """Count of checks per checker class."""
        return {
            ck.value: len(checks)
            for ck, checks in self._by_checker.items()
            if checks
        }

    # -- Serialization --------------------------------------------------------

    def to_list(self) -> List[dict]:
        """Serialize all checks to plain dicts."""
        return [c.to_dict() for c in self.list_all()]

    # -- Validation -----------------------------------------------------------

    def validate(self) -> List[str]:
        """Validate catalog integrity. Returns list of issues (empty = valid)."""
        issues: List[str] = []

        # Uniqueness
        ids = set()
        duplicates = set()
        for entry in self._by_id.values():
            if entry.check_id in ids:
                duplicates.add(entry.check_id)
            ids.add(entry.check_id)
        if duplicates:
            issues.append("Duplicate IDs: %s" % sorted(duplicates))

        # Count
        if self._count != 99:
            issues.append("Expected 99 checks, got %d" % self._count)

        # All entries have required fields
        for entry in self._by_id.values():
            if not entry.check_id:
                issues.append("Empty check_id on entry %s" % entry.name)
            if not entry.name:
                issues.append("Empty name on entry %s" % entry.check_id)
            if not entry.description:
                issues.append("Empty description on %s" % entry.check_id)
            if not entry.baseline_ref:
                issues.append("Empty baseline_ref on %s" % entry.check_id)
            if not entry.source_document:
                issues.append("Empty source_document on %s" % entry.check_id)

        return issues
