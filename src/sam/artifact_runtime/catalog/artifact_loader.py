"""ArtifactLoader — loader TANPA baca file (in-memory only)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .artifact_catalog import ArtifactCatalog
from ..model.artifact import Artifact


@dataclass(frozen=True)
class ArtifactLoadResult:
    loaded: int = 0
    catalog: ArtifactCatalog = None
    external_calls: int = 0


class ArtifactLoader:
    """Loader artifact. TIDAK membaca file/disk; hanya data in-memory."""

    def load(self, artifacts: Tuple[Artifact, ...] = ()) -> ArtifactLoadResult:
        cat = ArtifactCatalog()
        for a in artifacts:
            cat = cat.add(a)
        return ArtifactLoadResult(loaded=len(artifacts), catalog=cat,
                                  external_calls=0)
