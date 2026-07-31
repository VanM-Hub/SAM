"""Knowledge Index — indeks knowledge (Sprint 184).

Phase XVIII — Knowledge Runtime.
Read-only, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from ..foundation.knowledge_registry import KnowledgeRegistry


@dataclass(frozen=True)
class KnowledgeIndex:
    """Indeks knowledge (immutable)."""
    tag_index: Dict[str, List[str]] = field(default_factory=dict)


class KnowledgeIndexer:
    """Pembuat indeks knowledge. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def build(self) -> KnowledgeIndex:
        index: Dict[str, List[str]] = {}
        for kid in self._registry.list_ids():
            d = self._registry.find(kid)
            if d is None:
                continue
            for tag in d.tags:
                index.setdefault(tag, []).append(kid)
        return KnowledgeIndex(tag_index=index)

    def find_by_tag(self, tag: str) -> List[str]:
        return list(self.build().tag_index.get(tag, []))
