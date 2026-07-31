"""Sprint 267 - Certification: manifest (manifest sertifikasi)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CertificationManifest:
    """Manifest immutable hasil sertifikasi."""

    version: str = "28.0.0"
    dimensions: Tuple[str, ...] = ()
    status: str = "pending"

    def as_dict(self) -> dict:
        return {
            "version": self.version,
            "dimensions": list(self.dimensions),
            "status": self.status,
        }
