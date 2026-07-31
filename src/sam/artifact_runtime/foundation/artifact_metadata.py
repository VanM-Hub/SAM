"""ArtifactMetadata — metadata artifact runtime."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactMetadata:
    """Metadata representasi artifact (immutable)."""
    phase: str = "XXIII"
    version: str = "23.0.0"
    runtime: str = "artifact"
    preview_only: bool = True
    no_storage: bool = True
