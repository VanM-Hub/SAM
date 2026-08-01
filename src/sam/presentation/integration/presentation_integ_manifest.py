"""Sprint 279 - Desktop Integration: manifest (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PresentationIntegManifest:
    """Manifes integrasi desktop (metadata pipeline)."""

    runtime: str = "presentation"
    version: str = "29.0.0"
    pipeline: Tuple[str, ...] = (
        "mission_runtime",
        "runtime_kernel",
        "execution_runtime",
        "dashboard",
    )

    def as_dict(self) -> dict:
        return {
            "runtime": self.runtime,
            "version": self.version,
            "pipeline": list(self.pipeline),
        }
