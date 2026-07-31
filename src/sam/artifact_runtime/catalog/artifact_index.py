"""ArtifactIndex — indeks artifact (immutable, read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactIndex:
    """Indeks nama artifact. Immutable."""
    ids: Tuple[str, ...] = ()


class ArtifactIndexer:
    """Penyusun indeks artifact. Deterministic."""

    def index(self, names: Tuple[str, ...]) -> ArtifactIndex:
        return ArtifactIndex(tuple(sorted(names)))
