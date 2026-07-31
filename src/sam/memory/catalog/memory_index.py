"""Memory Index — indeks memori (Sprint 176).

Phase XVII — Memory Runtime.
Read-only, deterministic.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from ..foundation.memory_registry import MemoryRegistry


@dataclass(frozen=True)
class MemoryIndex:
    """Indeks memori (immutable)."""
    tag_index: Dict[str, List[str]] = field(default_factory=dict)


class MemoryIndexer:
    """Pembuat indeks memori. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def build(self) -> MemoryIndex:
        index: Dict[str, List[str]] = {}
        for mid in self._registry.list_ids():
            d = self._registry.find(mid)
            if d is None:
                continue
            for tag in d.tags:
                index.setdefault(tag, []).append(mid)
        return MemoryIndex(tag_index=index)

    def find_by_tag(self, tag: str) -> List[str]:
        return list(self.build().tag_index.get(tag, []))
