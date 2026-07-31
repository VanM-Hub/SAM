"""ArtifactManifest — manifest artifact (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ArtifactManifest:
    """Manifest daftar artifact. Immutable & read-only."""
    name: str
    artifacts: Tuple[str, ...] = ()
    no_storage: bool = True
    no_publish: bool = True
    preview_only: bool = True
