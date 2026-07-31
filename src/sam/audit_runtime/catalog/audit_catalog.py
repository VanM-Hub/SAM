"""Audit Catalog — katalog audit read-only (Sprint 216).

Read-only, tanpa file, tanpa cache. Immutable records.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from ..foundation.audit_descriptor import AuditDescriptor


@dataclass(frozen=True)
class AuditCatalog:
    """Katalog audit immutable (in-memory read-only)."""
    _entries: Dict[str, AuditDescriptor] = field(default_factory=dict, repr=False)

    def add(self, audit: AuditDescriptor) -> "AuditCatalog":
        return AuditCatalog(_entries={**self._entries, audit.audit_id: audit})

    def get(self, audit_id: str) -> AuditDescriptor:
        return self._entries.get(audit_id)

    def all_entries(self) -> List[AuditDescriptor]:
        return list(self._entries.values())

    def by_category(self, category: str) -> List[AuditDescriptor]:
        return [a for a in self._entries.values() if a.category == category]

    def count(self) -> int:
        return len(self._entries)
