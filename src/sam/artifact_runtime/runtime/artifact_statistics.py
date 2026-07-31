"""ArtifactStatistics — statistik representasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactStatistics:
    total: int = 0
    by_kind: Tuple = ()
    external_calls: int = 0


class ArtifactCollector:
    """Kolektor statistik artifact. Immutable & deterministic."""

    def collect(self, kinds: Tuple[str, ...] = ()) -> ArtifactStatistics:
        counts = {}
        for k in kinds:
            counts[k] = counts.get(k, 0) + 1
        by_kind = tuple(sorted(counts.items()))
        return ArtifactStatistics(total=len(kinds), by_kind=by_kind,
                                  external_calls=0)
