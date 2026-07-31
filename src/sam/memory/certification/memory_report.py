"""Memory Report — laporan sertifikasi memori (Sprint 178)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .memory_certification import MemoryCertificationResult  # noqa: F401


@dataclass(frozen=True)
class MemoryCertificationReport:
    """Laporan sertifikasi memori (immutable)."""
    certified: bool = False
    score: float = 0.0
    headline: str = ""
    details: List[str] = field(default_factory=list)


class MemoryCertificationReporter:
    """Reporter sertifikasi memori. Read-only."""

    def report(self, result: MemoryCertificationResult) -> MemoryCertificationReport:
        details = [
            f"{c.name}: {'PASS' if c.passed else 'FAIL'} - {c.detail}"
            for c in result.criteria
        ]
        headline = "Memory Runtime CERTIFIED" if result.certified \
            else "Memory Runtime NOT certified"
        return MemoryCertificationReport(
            certified=result.certified, score=result.score,
            headline=headline, details=details,
        )
