"""Provider Matrix — matriks provider (Sprint 247).

Program B — Model Runtime Integration.
Matriks read-only provider x kapabilitas. Belum network. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from .provider_profile import ProviderProfile


@dataclass(frozen=True)
class ProviderMatrix:
    """Matriks provider (immutable). Informasi statis."""
    matrix_id: str = "provider-matrix"
    profiles: List[ProviderProfile] = field(default_factory=list)
    rows: Dict[str, Tuple[str, ...]] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "matrix_id": self.matrix_id,
            "profiles": [p.as_dict() for p in self.profiles],
            "rows": {k: list(v) for k, v in self.rows.items()},
        }

    def provider(self, name: str) -> ProviderProfile | None:
        for p in self.profiles:
            if p.provider == name:
                return p
        return None
