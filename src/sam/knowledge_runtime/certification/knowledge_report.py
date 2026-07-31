"""Knowledge Report — laporan sertifikasi knowledge (Sprint 186)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .knowledge_certification import KnowledgeCertificationResult  # noqa: F401


@dataclass(frozen=True)
class KnowledgeCertificationReport:
    """Laporan sertifikasi knowledge (immutable)."""
    certified: bool = False
    score: float = 0.0
    headline: str = ""
    details: List[str] = field(default_factory=list)


class KnowledgeCertificationReporter:
    """Reporter sertifikasi knowledge. Read-only."""

    def report(self, result: KnowledgeCertificationResult) -> KnowledgeCertificationReport:
        details = [
            f"{c.name}: {'PASS' if c.passed else 'FAIL'} - {c.detail}"
            for c in result.criteria
        ]
        headline = "Knowledge Runtime CERTIFIED" if result.certified \
            else "Knowledge Runtime NOT certified"
        return KnowledgeCertificationReport(
            certified=result.certified, score=result.score,
            headline=headline, details=details,
        )
