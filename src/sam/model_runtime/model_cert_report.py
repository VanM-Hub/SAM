"""Model Report — laporan sertifikasi model (Sprint 248).

Program B — Model Runtime Integration.
Laporan sertifikasi 7 dimensi. Immutable, deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .model_score import ModelScoreSet


@dataclass(frozen=True)
class ModelCertificationReport:
    """Laporan sertifikasi (immutable)."""
    report_id: str
    model_id: str = ""
    passed: bool = False
    dimensions_total: int = 7
    dimensions_passed: int = 0
    score_set: ModelScoreSet = field(default_factory=ModelScoreSet)
    notes: List[str] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {
            "report_id": self.report_id,
            "model_id": self.model_id,
            "passed": self.passed,
            "dimensions_total": self.dimensions_total,
            "dimensions_passed": self.dimensions_passed,
            "scores": self.score_set.as_dict(),
            "notes": list(self.notes),
        }
