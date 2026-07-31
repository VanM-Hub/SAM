"""ArtifactSummary — ringkasan representasi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactSummary:
    total: int = 0
    kinds: Tuple[str, ...] = ()
    no_storage: bool = True
    preview_only: bool = True


class ArtifactSummarizer:
    """Penyusun ringkasan artifact. Immutable & deterministic."""

    def summarize(self, names: Tuple[str, ...],
                  kinds: Tuple[str, ...] = ()) -> ArtifactSummary:
        return ArtifactSummary(total=len(names), kinds=tuple(kinds),
                               no_storage=True, preview_only=True)
