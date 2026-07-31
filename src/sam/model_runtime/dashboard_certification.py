"""Dashboard Certification — bridge dashboard <-> model cert (Sprint 248).

Program B — Model Runtime Integration.
Read-only bridge; sertifikasi, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .model_cert_report import ModelCertificationReport


@dataclass(frozen=True)
class DashboardCertificationRow:
    """Satu baris sertifikasi pada dashboard (immutable)."""
    row_id: str
    model_id: str
    passed: bool = False
    dimensions_passed: int = 0
    dimensions_total: int = 7
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "model_id": self.model_id,
            "passed": self.passed,
            "dimensions_passed": self.dimensions_passed,
            "dimensions_total": self.dimensions_total,
            "external_calls": self.external_calls,
        }


class DashboardCertification:
    """Bridge dashboard <-> model certification. Read-only, no-network."""

    def __init__(self) -> None:
        self._rows: List[DashboardCertificationRow] = []

    def add(self, report: ModelCertificationReport) -> None:
        self._rows.append(DashboardCertificationRow(
            row_id=f"dcert-{len(self._rows) + 1}",
            model_id=report.model_id,
            passed=report.passed,
            dimensions_passed=report.dimensions_passed,
            dimensions_total=report.dimensions_total,
            external_calls=0,
        ))

    def rows(self) -> List[DashboardCertificationRow]:
        return list(self._rows)

    def summary(self) -> Dict[str, object]:
        passed = sum(1 for r in self._rows if r.passed)
        return {
            "models": len(self._rows),
            "passed": passed,
            "failed": len(self._rows) - passed,
            "external_calls": 0,
        }
