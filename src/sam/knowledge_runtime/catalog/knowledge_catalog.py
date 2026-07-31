"""Knowledge Catalog — katalog knowledge (Sprint 184).

Phase XVIII — Knowledge Runtime.
Read-only, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.knowledge_registry import KnowledgeRegistry


@dataclass(frozen=True)
class KnowledgeCatalogEntry:
    """Entri katalog knowledge (immutable)."""
    knowledge_id: str
    name: str = ""
    category: str = "general"
    version: str = "1.0.0"
    tags: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class KnowledgeCatalogSearchResult:
    """Hasil pencarian katalog (immutable)."""
    query: str = ""
    entries: List[KnowledgeCatalogEntry] = field(default_factory=list)


class KnowledgeCatalog:
    """Katalog knowledge. Read-only, deterministic."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def _entries(self) -> List[KnowledgeCatalogEntry]:
        entries = []
        for kid in self._registry.list_ids():
            d = self._registry.find(kid)
            if d is not None:
                entries.append(KnowledgeCatalogEntry(
                    knowledge_id=kid, name=d.name, category=d.category,
                    version=d.version, tags=list(d.tags),
                ))
        return entries

    def all_entries(self) -> List[KnowledgeCatalogEntry]:
        return self._entries()

    def search(self, query: str = "") -> KnowledgeCatalogSearchResult:
        entries = self._entries()
        q = query.lower()
        if q:
            entries = [
                e for e in entries
                if q in e.name.lower() or q in e.category.lower()
                or any(q in t.lower() for t in e.tags)
            ]
        return KnowledgeCatalogSearchResult(query=query, entries=entries)

    def by_category(self, category: str) -> List[KnowledgeCatalogEntry]:
        return [e for e in self._entries() if e.category == category]

    def count(self) -> int:
        return len(self._entries())
