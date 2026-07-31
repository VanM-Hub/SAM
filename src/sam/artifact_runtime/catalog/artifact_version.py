"""ArtifactVersion — versi artifact (read-only)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactVersionInfo:
    version: str = "23.0.0"
    phase: str = "XXIII"


class ArtifactVersionProvider:
    """Penyedia versi artifact. Deterministic."""

    def version(self) -> ArtifactVersionInfo:
        return ArtifactVersionInfo()
