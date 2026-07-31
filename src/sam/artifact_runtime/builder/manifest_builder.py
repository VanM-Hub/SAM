"""ManifestBuilder — menyusun ArtifactManifest (no storage)."""
from __future__ import annotations

from typing import Tuple

from ..model.artifact_manifest import ArtifactManifest


class ManifestBuilder:
    """Builder manifest artifact. Immutable & read-only."""

    def build(self, name: str,
              artifacts: Tuple[str, ...] = ()) -> ArtifactManifest:
        return ArtifactManifest(name=name, artifacts=tuple(artifacts))
