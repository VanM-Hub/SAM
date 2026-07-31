"""Policy Report — laporan sertifikasi policy (Sprint 210)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .policy_certification import PolicyCertificationResult  # noqa: F401


@dataclass(frozen=True)
class PolicyCertificationReport:
    """Laporan sertifikasi policy (immutable)."""
    certified: bool = False
    score: float = 0.0
    headline: str = ""
    details: List[str] = field(default_factory=list)


class PolicyCertificationReporter:
    """Reporter sertifikasi. Read-only."""

    def report(self, result: PolicyCertificationResult) -> PolicyCertificationReport:
        details = [
            f"{c.name}: {'PASS' if c.passed else 'FAIL'} - {c.detail}"
            for c in result.criteria
        ]
        headline = "Policy Runtime CERTIFIED" if result.certified \
            else "Policy Runtime NOT certified"
        return PolicyCertificationReport(
            certified=result.certified, score=result.score,
            headline=headline, details=details,
        )
