"""Audit Report — laporan sertifikasi audit (Sprint 218)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .audit_certification import AuditCertificationResult


@dataclass(frozen=True)
class AuditCertificationReport:
    """Laporan sertifikasi immutable."""
    certified: bool = False
    score: float = 0.0
    headline: str = ""


class AuditCertificationReporter:
    """Reporter sertifikasi audit read-only."""

    def report(self, result: AuditCertificationResult) -> AuditCertificationReport:
        headline = "CERTIFIED" if result.certified else "NOT-CERTIFIED"
        return AuditCertificationReport(
            certified=result.certified, score=result.score, headline=headline)
