"""PreviewBuilder — menyusun ArtifactPreviewDTO (preview-only)."""
from __future__ import annotations

from dataclasses import FrozenInstanceError

from .artifact_builder import ArtifactPreviewDTO


class PreviewBuilder:
    """Builder preview artifact. Memastikan tidak tersimpan/dipublikasi."""

    def preview(self, name: str, kind: str = "report") -> ArtifactPreviewDTO:
        dto = ArtifactPreviewDTO(name=name, kind=kind,
                                 stored=False, published=False,
                                 external_calls=0)
        if dto.stored or dto.published or dto.external_calls != 0:
            raise FrozenInstanceError("preview must be stored=False, published=False, external_calls=0")
        return dto
