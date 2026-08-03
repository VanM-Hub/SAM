"""Compliance check registry.

Manages registration, lookup, and organization of compliance checks.
Per P1-001 Check Registry specification.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from ..models.check_model import ComplianceCheck
from ..models.level import ComplianceLevel
from ..models.category import ComplianceCategory
from ..exceptions.compliance_errors import CheckNotFoundError, DuplicateCheckError, RegistryError


class ComplianceRegistry:
    """Registry for compliance checks.

    Stores checks indexed by check_id.
    Supports: register, unregister, find, list_all, list_by_level, list_by_category.

    Deterministic: same input produces same output in all query operations.
    """

    def __init__(self) -> None:
        self._checks: Dict[str, ComplianceCheck] = {}

    def register(self, check: ComplianceCheck) -> None:
        """Register a compliance check.

        Raises DuplicateCheckError if check_id already exists.
        """
        if check.check_id in self._checks:
            raise DuplicateCheckError(check.check_id)
        self._checks[check.check_id] = check

    def register_all(self, checks: List[ComplianceCheck]) -> None:
        """Register multiple checks at once.

        Raises DuplicateCheckError if any check_id duplicates.
        """
        seen = set()
        for c in checks:
            if c.check_id in self._checks or c.check_id in seen:
                raise DuplicateCheckError(c.check_id)
            seen.add(c.check_id)
        for c in checks:
            self._checks[c.check_id] = c

    def unregister(self, check_id: str) -> bool:
        """Remove a check from the registry. Returns True if removed, False if not found."""
        if check_id in self._checks:
            del self._checks[check_id]
            return True
        return False

    def find(self, check_id: str) -> Optional[ComplianceCheck]:
        """Find a check by ID. Returns None if not found."""
        return self._checks.get(check_id)

    def get(self, check_id: str) -> ComplianceCheck:
        """Get a check by ID. Raises CheckNotFoundError if not found."""
        check = self._checks.get(check_id)
        if check is None:
            raise CheckNotFoundError(check_id)
        return check

    def list_all(self) -> List[ComplianceCheck]:
        """List all registered checks, sorted by check_id (deterministic order)."""
        return sorted(self._checks.values(), key=lambda c: c.check_id)

    def list_by_level(self, level: ComplianceLevel) -> List[ComplianceCheck]:
        """List checks at a specific compliance level, sorted by check_id."""
        return sorted(
            [c for c in self._checks.values() if c.level == level],
            key=lambda c: c.check_id,
        )

    def list_by_category(self, category: ComplianceCategory) -> List[ComplianceCheck]:
        """List checks for a specific category, sorted by check_id."""
        return sorted(
            [c for c in self._checks.values() if c.category == category],
            key=lambda c: c.check_id,
        )

    def group_by_level(self) -> Dict[ComplianceLevel, List[ComplianceCheck]]:
        """Group all checks by compliance level.

        Returns dict with levels as keys, sorted check lists as values.
        Empty levels are included.
        """
        result: Dict[ComplianceLevel, List[ComplianceCheck]] = {}
        for lvl in ComplianceLevel.all_levels():
            checks = self.list_by_level(lvl)
            result[lvl] = checks
        return result

    def group_by_category(self) -> Dict[ComplianceCategory, List[ComplianceCheck]]:
        """Group all checks by category.

        Returns dict with categories as keys, sorted check lists as values.
        Empty categories are included.
        """
        result: Dict[ComplianceCategory, List[ComplianceCheck]] = {}
        for cat in ComplianceCategory.all_categories():
            checks = self.list_by_category(cat)
            result[cat] = checks
        return result

    def count(self) -> int:
        """Return total number of registered checks."""
        return len(self._checks)

    def count_by_level(self, level: ComplianceLevel) -> int:
        """Return number of checks at a specific level."""
        return len(self.list_by_level(level))

    def count_by_category(self, category: ComplianceCategory) -> int:
        """Return number of checks for a specific category."""
        return len(self.list_by_category(category))

    def clear(self) -> None:
        """Remove all registered checks."""
        self._checks.clear()

    def is_empty(self) -> bool:
        """Return True if no checks are registered."""
        return len(self._checks) == 0

    def check_ids(self) -> List[str]:
        """Return all check IDs in sorted order."""
        return sorted(self._checks.keys())

    def __len__(self) -> int:
        return self.count()

    def __contains__(self, check_id: str) -> bool:
        return check_id in self._checks
