"""Cognitive Statistics — statistika runtime kognitif (Sprint 191)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.cognitive_registry import CognitiveRegistry


@dataclass(frozen=True)
class CognitiveStatisticsItem:
    """Statistik per unit (immutable)."""
    cognitive_id: str = ""
    registered: bool = False


@dataclass(frozen=True)
class CognitiveStatistics:
    """Statistik kognitif (immutable)."""
    total: int = 0
    registered: int = 0
    items: List[CognitiveStatisticsItem] = field(default_factory=list)


class CognitiveStatisticsCollector:
    """Collector statistik. Read-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def collect(self) -> CognitiveStatistics:
        descs = self._registry.all()
        items = [
            CognitiveStatisticsItem(cognitive_id=d.id, registered=True)
            for d in descs
        ]
        return CognitiveStatistics(
            total=len(items), registered=len(items), items=items,
        )
