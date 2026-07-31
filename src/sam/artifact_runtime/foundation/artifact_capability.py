"""ArtifactCapability — kemampuan artifact runtime (no storage/no publish)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ArtifactCapability:
    """Kapabilitas representasi artifact (immutable)."""
    immutable: bool = True
    no_storage: bool = True
    no_publish: bool = True
    no_execute: bool = True
    deterministic: bool = True
    preview_only: bool = True
