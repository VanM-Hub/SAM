"""Knowledge Summary — ringkasan knowledge (Sprint 183)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.knowledge_registry import KnowledgeRegistry


@dataclass(frozen=True)
class KnowledgeSummary:
    """Ringkasan knowledge runtime (immutable)."""
    version: str = "1.0.0"
    total_knowledge: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)
    external_calls: int = 0


class KnowledgeSummarizer:
    """Summarizer knowledge. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def summary(self) -> KnowledgeSummary:
        s = self._registry.summary()
        return KnowledgeSummary(
            version="1.0.0",
            total_knowledge=s.total,
            by_category=s.by_category,
            external_calls=0,
        )
