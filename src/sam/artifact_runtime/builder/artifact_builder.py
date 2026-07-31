"""ArtifactBuilder — menyusun Artifact DTO (no storage/no publish)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from ..model.artifact import Artifact
from ..model.artifact_validator import ArtifactValidator


@dataclass(frozen=True)
class ArtifactBuildResult:
    """Hasil build artifact (immutable)."""
    artifact: Optional[Artifact] = None
    ok: bool = False
    error: str = ""


@dataclass(frozen=True)
class ArtifactPreviewDTO:
    """Preview DTO — artifact belum dipublikasi/disimpan."""
    name: str = ""
    kind: str = ""
    stored: bool = False
    published: bool = False
    external_calls: int = 0


class ArtifactBuilder:
    """Builder HANYA menyusun DTO. Tidak menulis file, tidak mempublikasi."""

    def __init__(self) -> None:
        self._validator = ArtifactValidator()

    def build(self, name: str, kind: str = "report", content: str = "") -> ArtifactBuildResult:
        artifact = Artifact(name=name, kind=kind, content=content)
        validation = self._validator.validate(artifact)
        if not validation.valid:
            return ArtifactBuildResult(artifact=None, ok=False,
                                       error=";".join(validation.errors))
        return ArtifactBuildResult(artifact=artifact, ok=True)
