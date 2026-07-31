"""ArtifactMetrics — metrik representasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple, Dict


@dataclass(frozen=True)
class ArtifactMetricSample:
    kind: str = "artifact"
    value: int = 0


@dataclass(frozen=True)
class ArtifactMetrics:
    samples: Tuple[ArtifactMetricSample, ...] = ()
    external_calls: int = 0


class ArtifactMetricsCollector:
    """Kolektor metrik artifact. Deterministic & read-only."""

    def collect(self, counts: Dict[str, int] = None) -> ArtifactMetrics:
        counts = counts or {}
        samples = tuple(
            ArtifactMetricSample(kind=k, value=v)
            for k, v in sorted(counts.items())
        )
        return ArtifactMetrics(samples=samples, external_calls=0)
