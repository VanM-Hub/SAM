"""ArtifactRuntime — representasi artifact (preview-only, no storage)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..builder.artifact_builder import ArtifactBuilder, ArtifactPreviewDTO
from ..model.artifact_validator import ArtifactValidator


@dataclass(frozen=True)
class ArtifactRunResult:
    """Hasil run artifact (immutable, preview)."""
    name: str = ""
    ok: bool = False
    preview: Optional[ArtifactPreviewDTO] = None
    external_calls: int = 0


class ArtifactRuntime:
    """Runtime representasi artifact. Preview-only, no storage, no publish."""

    def __init__(self) -> None:
        self._builder = ArtifactBuilder()
        self._validator = ArtifactValidator()

    def run(self, name: str, kind: str = "report") -> ArtifactRunResult:
        res = self._builder.build(name, kind)
        if not res.ok:
            return ArtifactRunResult(name=name, ok=False, external_calls=0)
        artifact = res.artifact
        preview = ArtifactPreviewDTO(name=artifact.name, kind=artifact.kind,
                                     stored=False, published=False,
                                     external_calls=0)
        return ArtifactRunResult(name=artifact.name, ok=True,
                                 preview=preview, external_calls=0)
