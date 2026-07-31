"""ArtifactValidator — validasi artifact (no storage/no publish/no execute)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from .artifact import Artifact


@dataclass(frozen=True)
class ArtifactValidation:
    valid: bool = True
    errors: tuple = ()


@dataclass(frozen=True)
class ArtifactValidator:
    """Validator representasi artifact. Immutable & deterministic."""

    def validate(self, artifact: Optional[Artifact]) -> ArtifactValidation:
        if artifact is None:
            return ArtifactValidation(False, ("artifact is None",))
        if not artifact.name:
            return ArtifactValidation(False, ("name required",))
        if artifact.no_storage is not True:
            return ArtifactValidation(False, ("no_storage must be True",))
        if artifact.no_publish is not True:
            return ArtifactValidation(False, ("no_publish must be True",))
        if artifact.immutable is not True:
            return ArtifactValidation(False, ("immutable must be True",))
        return ArtifactValidation(True, ())
