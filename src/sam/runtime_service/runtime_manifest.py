"""RuntimeManifest (Sprint 271).

Program D - Runtime Services & Deployment.
Manifest runtime (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class RuntimeManifest:
    """Manifest runtime (immutable)."""
    name: str
    version: str = "27.0.0"
    entry_point: str = "sam.runtime_service"
    layers: List[str] = field(default_factory=list)
    certifications: int = 0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "version": self.version,
            "entry_point": self.entry_point,
            "layers": list(self.layers),
            "certifications": self.certifications,
        }
