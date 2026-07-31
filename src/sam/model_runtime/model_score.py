"""Model Score — skor sertifikasi model (Sprint 248).

Program B — Model Runtime Integration.
Sertifikasi 7 dimensi. Immutable, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class ModelScore:
    """Skor sertifikasi (immutable). Dimensi-divisi 7."""
    dimension: str
    score: float = 0.0
    passed: bool = False
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "dimension": self.dimension,
            "score": self.score,
            "passed": self.passed,
            "detail": self.detail,
        }


@dataclass(frozen=True)
class ModelScoreSet:
    """Kumpulan skor (immutable)."""
    scores: Dict[str, ModelScore] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {name: s.as_dict() for name, s in self.scores.items()}
