"""Agent Report — laporan sertifikasi agent (Sprint 163).

Agent Runtime — laporan read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .agent_certification import CertificationResult  # noqa: F401


@dataclass(frozen=True)
class AgentReport:
    """Laporan sertifikasi (immutable)."""
    certified: bool = False
    score: float = 0.0
    headline: str = ""
    details: List[str] = field(default_factory=list)


class AgentReporter:
    """Reporter sertifikasi. Read-only."""

    def report(self, result: CertificationResult) -> AgentReport:
        details = [
            f"{c.name}: {'PASS' if c.passed else 'FAIL'} - {c.detail}"
            for c in result.criteria
        ]
        headline = "Agent Runtime CERTIFIED" if result.certified \
            else "Agent Runtime NOT certified"
        return AgentReport(
            certified=result.certified,
            score=result.total_score,
            headline=headline,
            details=details,
        )
