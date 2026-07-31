"""ArtifactReference — referensi traceable artifact (immutable)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactReference:
    """Referensi traceable ke artifact. Immutable & read-only."""
    name: str
    kind: str = "reference"
    traceable: bool = True
    immutable: bool = True
    no_storage: bool = True
