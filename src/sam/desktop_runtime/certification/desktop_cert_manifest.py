"""Sprint 278 - Desktop Certification: manifest (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DesktopCertManifest:
    """Manifes sertifikasi desktop (metadata, tanpa IO)."""

    program: str = "F"
    version: str = "29.0.0"
    dimensions: Tuple[str, ...] = (
        "composition_only",
        "preview_only",
        "deterministic_sync",
        "no_execute_self",
        "immutable_dto",
        "readonly_bridges",
        "no_llm_inference",
    )

    def as_dict(self) -> dict:
        return {
            "program": self.program,
            "version": self.version,
            "dimensions": list(self.dimensions),
        }
