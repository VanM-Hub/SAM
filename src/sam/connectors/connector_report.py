"""Connector Report — engine laporan sertifikasi connector.

Sprint 122 — Connector Certification.
Laporan akhir sertifikasi (read-only, immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_certification import CertificationResult
from .connector_score import ConnectorScore


@dataclass(frozen=True)
class ConnectorReport:
    """Laporan akhir connector runtime."""
    certified: bool = False
    score: float = 0.0
    detail: str = ""


class ConnectorReporter:
    """Bangun laporan sertifikasi."""

    def report(self, cert: CertificationResult) -> ConnectorReport:
        return ConnectorReport(cert.certified, cert.score,
                               f"{cert.score} pts, certified" if cert.certified
                               else f"{cert.score} pts, not certified")
