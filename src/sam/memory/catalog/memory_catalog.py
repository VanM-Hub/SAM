"""Memory Catalog — katalog memori (Sprint 176).

Phase XVII — Memory Runtime.
Read-only, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.memory_registry import MemoryRegistry


@dataclass(frozen=True)
class MemoryCatalogEntry:
    """Entri katalog memori (immutable)."""
    memory_id: str
    name: str = ""
    category: str = "general"
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class MemoryCatalogSearchResult:
    """Hasil pencarian katalog (immutable)."""
    query: str = ""
    entries: List[MemoryCatalogEntry] = field(default_factory=list)


class MemoryCatalog:
    """Katalog memori. Read-only, deterministic."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def _entries(self) -> List[MemoryCatalogEntry]:
        entries = []
        for mid in self._registry.list_ids():
            d = self._registry.find(mid)
            if d is not None:
                entries.append(MemoryCatalogEntry(
                    memory_id=mid, name=d.name, category=d.category,
                    version=d.version, tags=list(d.tags),
                ))
        return entries

    def all_entries(self) -> List[MemoryCatalogEntry]:
        return self._entries()

    def search(self, query: str = "") -> MemoryCatalogSearchResult:
        entries = self._entries()
        q = query.lower()
        if q:
            entries = [
                e for e in entries
                if q in e.name.lower() or q in e.category.lower()
                or any(q in t.lower() for t in e.tags)
            ]
        return MemoryCatalogSearchResult(query=query, entries=entries)

    def by_category(self, category: str) -> List[MemoryCatalogEntry]:
        return [e for e in self._entries() if e.category == category]

    def count(self) -> int:
        return len(self._entries())
