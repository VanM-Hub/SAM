"""Memory Metrics — metrik memori (Sprint 177).

Phase XVII — Memory Runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.memory_registry import MemoryRegistry


@dataclass(frozen=True)
class MemoryMetricSample:
    """Satu sampel metrik memori (immutable)."""
    memory_id: str
    preview_count: int = 0
    external_calls: int = 0
    healthy: bool = False


@dataclass(frozen=True)
class MemoryMetrics:
    """Metrik memori (immutable)."""
    total: int = 0
    external_calls: int = 0
    samples: List[MemoryMetricSample] = field(default_factory=list)


class MemoryMetricsCollector:
    """Collector metrik memori. Read-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def collect(self) -> MemoryMetrics:
        samples = []
        for mid in self._registry.list_ids():
            d = self._registry.find(mid)
            healthy = d is not None and bool(self._registry.get_capabilities(mid))
            samples.append(MemoryMetricSample(
                memory_id=mid, preview_count=0, external_calls=0, healthy=healthy,
            ))
        return MemoryMetrics(
            total=len(samples), external_calls=0, samples=samples,
        )
