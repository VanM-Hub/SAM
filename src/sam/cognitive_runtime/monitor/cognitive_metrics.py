"""Cognitive Metrics — metrik kognitif (Sprint 193)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.cognitive_registry import CognitiveRegistry


@dataclass(frozen=True)
class CognitiveMetricSample:
    """Sampel metrik per unit (immutable)."""
    cognitive_id: str = ""
    registered: bool = False
    preview_count: int = 0
    external_calls: int = 0


@dataclass(frozen=True)
class CognitiveMetrics:
    """Metrik kognitif agregat (immutable)."""
    total: int = 0
    external_calls: int = 0
    samples: List[CognitiveMetricSample] = field(default_factory=list)


class CognitiveMetricsCollector:
    """Collector metrik. Read-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def collect(self) -> CognitiveMetrics:
        samples = [
            CognitiveMetricSample(cognitive_id=d.id, registered=True,
                                  preview_count=0, external_calls=0)
            for d in self._registry.all()
        ]
        return CognitiveMetrics(total=len(samples), external_calls=0, samples=samples)
