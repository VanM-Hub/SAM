"""Knowledge Snapshot — snapshot knowledge (Sprint 185).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.knowledge_registry import KnowledgeRegistry


@dataclass(frozen=True)
class KnowledgeSnapshot:
    """Snapshot knowledge (immutable)."""
    knowledge_id: str = ""
    total: int = 0
    categories: Dict[str, int] = field(default_factory=dict)


class KnowledgeSnapshotter:
    """Pembuat snapshot knowledge. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def snapshot(self) -> KnowledgeSnapshot:
        s = self._registry.summary()
        return KnowledgeSnapshot(
            knowledge_id="all", total=s.total, categories=s.by_category,
        )
