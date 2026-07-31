"""ArtifactDescriptor — identitas artifact runtime."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactDescriptor:
    """Deskripsi representasi artifact (immutable)."""
    name: str
    category: str = "artifact"
    version: str = "23.0.0"
    provenance: bool = True
    traceable: bool = True
    deterministic: bool = True
    preview_only: bool = True
