"""Model Quality — kualitas model untuk sertifikasi (Sprint 248).

Program B — Model Runtime Integration.
Indikator kualitas deterministik. Immutable.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ModelQuality:
    """Kualitas model (immutable). Indikator statis/deterministik."""
    quality_id: str
    indicators: Dict[str, float] = field(default_factory=dict)
    overall: float = 1.0
    preview_only: bool = True

    def as_dict(self) -> dict:
        return {
            "quality_id": self.quality_id,
            "indicators": dict(self.indicators),
            "overall": self.overall,
            "preview_only": self.preview_only,
        }
