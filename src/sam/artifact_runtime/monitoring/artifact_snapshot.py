"""ArtifactSnapshot — snapshot representasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactSnapshot:
    names: Tuple[str, ...] = ()
    external_calls: int = 0


class ArtifactSnapshotter:
    """Penyusun snapshot artifact. Deterministic & read-only."""

    def snapshot(self, names: Tuple[str, ...] = ()) -> ArtifactSnapshot:
        return ArtifactSnapshot(names=tuple(names), external_calls=0)
