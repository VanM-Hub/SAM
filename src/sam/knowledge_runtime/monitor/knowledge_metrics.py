"""Knowledge Metrics — metrik knowledge (Sprint 185).

Phase XVIII — Knowledge Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.knowledge_registry import KnowledgeRegistry


@dataclass(frozen=True)
class KnowledgeMetricSample:
    """Satu sampel metrik knowledge (immutable)."""
    knowledge_id: str
    preview_count: int = 0
    external_calls: int = 0
    healthy: bool = False


@dataclass(frozen=True)
class KnowledgeMetrics:
    """Metrik knowledge (immutable)."""
    total: int = 0
    external_calls: int = 0
    samples: List[KnowledgeMetricSample] = field(default_factory=list)


class KnowledgeMetricsCollector:
    """Collector metrik knowledge. Read-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def collect(self) -> KnowledgeMetrics:
        samples = []
        for kid in self._registry.list_ids():
            d = self._registry.find(kid)
            healthy = d is not None and bool(self._registry.get_capabilities(kid))
            samples.append(KnowledgeMetricSample(
                knowledge_id=kid, preview_count=0, external_calls=0, healthy=healthy,
            ))
        return KnowledgeMetrics(
            total=len(samples), external_calls=0, samples=samples,
        )
