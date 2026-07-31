"""ReferenceBuilder — menyusun ArtifactReference (no storage)."""
from __future__ import annotations

from ..model.artifact_reference import ArtifactReference


class ReferenceBuilder:
    """Builder referensi artifact. Immutable & read-only."""

    def build(self, name: str) -> ArtifactReference:
        return ArtifactReference(name=name)
