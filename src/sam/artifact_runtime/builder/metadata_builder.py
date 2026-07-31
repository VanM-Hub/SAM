"""MetadataBuilder — menyusun ArtifactMetadata (no storage)."""
from __future__ import annotations

from ..model.artifact_metadata_model import ArtifactMetadata


class MetadataBuilder:
    """Builder metadata artifact. Immutable & read-only."""

    def build(self, name: str, kind: str = "artifact") -> ArtifactMetadata:
        return ArtifactMetadata(name=name, kind=kind)
