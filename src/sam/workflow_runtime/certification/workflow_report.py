"""Workflow Report — laporan sertifikasi workflow (Sprint 202)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .workflow_certification import WorkflowCertificationResult  # noqa: F401


@dataclass(frozen=True)
class WorkflowCertificationReport:
    """Laporan sertifikasi workflow (immutable)."""
    certified: bool = False
    score: float = 0.0
    headline: str = ""
    details: List[str] = field(default_factory=list)


class WorkflowCertificationReporter:
    """Reporter sertifikasi. Read-only."""

    def report(self, result: WorkflowCertificationResult) -> WorkflowCertificationReport:
        details = [
            f"{c.name}: {'PASS' if c.passed else 'FAIL'} - {c.detail}"
            for c in result.criteria
        ]
        headline = "Workflow Runtime CERTIFIED" if result.certified \
            else "Workflow Runtime NOT certified"
        return WorkflowCertificationReport(
            certified=result.certified, score=result.score,
            headline=headline, details=details,
        )
