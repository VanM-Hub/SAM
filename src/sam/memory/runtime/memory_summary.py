"""Memory Summary — ringkasan memori (Sprint 175)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict

from ..foundation.memory_registry import MemoryRegistry


@dataclass(frozen=True)
class MemorySummary:
    """Ringkasan memori runtime (immutable)."""
    version: str = "1.0.0"
    total_memories: int = 0
    by_category: Dict[str, int] = field(default_factory=dict)
    external_calls: int = 0


class MemorySummarizer:
    """Summarizer memori. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def summary(self) -> MemorySummary:
        s = self._registry.summary()
        return MemorySummary(
            version="1.0.0",
            total_memories=s.total,
            by_category=s.by_category,
            external_calls=0,
        )
