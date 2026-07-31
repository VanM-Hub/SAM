"""Skill Report — laporan sertifikasi skill (Sprint 170).

Phase XVI — Skill Runtime.
Read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .skill_certification import SkillCertificationResult  # noqa: F401


@dataclass(frozen=True)
class SkillCertificationReport:
    """Laporan sertifikasi skill (immutable)."""
    certified: bool = False
    score: float = 0.0
    headline: str = ""
    details: List[str] = field(default_factory=list)


class SkillCertificationReporter:
    """Reporter sertifikasi skill. Read-only."""

    def report(self, result: SkillCertificationResult) -> SkillCertificationReport:
        details = [
            f"{c.name}: {'PASS' if c.passed else 'FAIL'} - {c.detail}"
            for c in result.criteria
        ]
        headline = "Skill Runtime CERTIFIED" if result.certified \
            else "Skill Runtime NOT certified"
        return SkillCertificationReport(
            certified=result.certified, score=result.score,
            headline=headline, details=details,
        )
