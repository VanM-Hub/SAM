"""ArtifactContract — kontrak artifact runtime."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactContract:
    """Kontrak representasi artifact (immutable)."""
    preview_only: bool = True
    no_storage: bool = True
    no_publish: bool = True
    immutable: bool = True
    deterministic_hash: str = "sha256"
    required_fields: tuple = ("name", "kind", "content")
