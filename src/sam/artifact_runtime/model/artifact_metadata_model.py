"""ArtifactMetadataModel — struktur metadata artifact (immutable)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactMetadata:
    """Struktur metadata artifact runtime. Immutable & read-only."""
    name: str
    kind: str = "artifact"
    version: str = "23.0.0"
    traceable: bool = True
    immutable: bool = True
    no_storage: bool = True
    no_publish: bool = True
