"""Execution Cert Report (Sprint 258).

Program C - Real Execution Runtime.
Laporan immutable hasil sertifikasi (mirip model_cert_report pola Program B).
Catatan penamaan: dipakai kata "cert" untuk menghindari bentrok dengan
execution_report (Sprint 254).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .execution_score import ExecutionScoreSet


@dataclass(frozen=True)
class ExecutionCertReport:
    """Laporan sertifikasi (immutable)."""
    report_id: str
    passed: bool
    score_set: ExecutionScoreSet
    dimensions_passed: int = 0
    dimensions_total: int = 0

    def as_dict(self) -> dict:
        return {"report_id": self.report_id, "passed": self.passed,
                "score_set": self.score_set.as_dict(),
                "dimensions_passed": self.dimensions_passed,
                "dimensions_total": self.dimensions_total}
