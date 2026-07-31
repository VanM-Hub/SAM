"""Skill Catalog — katalog skill (Sprint 168).

Phase XVI — Skill Runtime.
Katalog menyediakan pencarian & penemuan skill. Read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..foundation.skill_registry import SkillRegistry
from ..foundation.skill_descriptor import SkillDescriptor


@dataclass(frozen=True)
class CatalogEntry:
    """Entri katalog (immutable)."""
    skill_id: str
    name: str = ""
    category: str = "general"
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CatalogSearchResult:
    """Hasil pencarian katalog (immutable)."""
    query: str = ""
    entries: List[CatalogEntry] = field(default_factory=list)


class SkillCatalog:
    """Katalog skill. Read-only, deterministik."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def all_entries(self) -> List[CatalogEntry]:
        return self._entries_via_descriptors()

    def _entries_via_descriptors(self) -> List[CatalogEntry]:
        entries = []
        for sid in self._registry.list_ids():
            d = self._registry.find(sid)
            if d is not None:
                entries.append(CatalogEntry(
                    skill_id=sid, name=d.name, category=d.category,
                    version=d.version, tags=list(d.tags),
                ))
        return entries

    def search(self, query: str = "") -> CatalogSearchResult:
        entries = self._entries_via_descriptors()
        q = query.lower()
        if q:
            entries = [
                e for e in entries
                if q in e.name.lower() or q in e.category.lower()
                or any(q in t.lower() for t in e.tags)
            ]
        return CatalogSearchResult(query=query, entries=entries)

    def by_category(self, category: str) -> List[CatalogEntry]:
        return [e for e in self._entries_via_descriptors()
                if e.category == category]

    def count(self) -> int:
        return len(self._entries_via_descriptors())
