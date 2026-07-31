"""Cognitive Report — laporan sertifikasi kognitif (Sprint 194)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .cognitive_certification import CognitiveCertificationResult  # noqa: F401


@dataclass(frozen=True)
class CognitiveCertificationReport:
    """Laporan sertifikasi kognitif (immutable)."""
    certified: bool = False
    score: float = 0.0
    headline: str = ""
    details: List[str] = field(default_factory=list)


class CognitiveCertificationReporter:
    """Reporter sertifikasi. Read-only."""

    def report(self, result: CognitiveCertificationResult) -> CognitiveCertificationReport:
        details = [
            f"{c.name}: {'PASS' if c.passed else 'FAIL'} - {c.detail}"
            for c in result.criteria
        ]
        headline = "Cognitive Runtime CERTIFIED" if result.certified \
            else "Cognitive Runtime NOT certified"
        return CognitiveCertificationReport(
            certified=result.certified, score=result.score,
            headline=headline, details=details,
        )
