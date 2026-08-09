"""Operational Intelligence API - WP-27 (MISSION-4.2 / IP-4.2-003).

Menyediakan antarmuka standar untuk seluruh capability Operational
Intelligence (investigasi, diagnosis, prediksi, rekomendasi, trust, risk).
API read-only, konsisten, dapat diintegrasikan, tanpa mutation.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .investigation_api import InvestigationAPI
from .diagnosis_api import DiagnosisAPI


@dataclass(frozen=True)
class IntelligenceSummary:
    """Ringkasan status capability intelligence."""

    investigation_count: int = 0
    diagnosis_count: int = 0
    recommendation_count: int = 0
    generation_time: str = ""

    def as_dict(self) -> dict:
        return {
            "investigation_count": self.investigation_count,
            "diagnosis_count": self.diagnosis_count,
            "recommendation_count": self.recommendation_count,
            "generation_time": self.generation_time,
        }


class OperationalIntelligenceAPI:
    """Public facade untuk Operational Intelligence (read-only)."""

    def __init__(
        self,
        *,
        investigations: InvestigationAPI,
        diagnoses: DiagnosisAPI,
        recommendations: Tuple[Dict[str, Any], ...] = (),
    ) -> None:
        self._investigations = investigations
        self._diagnoses = diagnoses
        self._recommendations = recommendations

    # --- Investigation ---
    def query_investigations(self):
        return self._investigations.query_investigations()

    def list_evidence(self, investigation_id: str):
        return self._investigations.list_evidence(investigation_id)

    # --- Diagnosis ---
    def list_diagnoses(self, investigation_id: Optional[str] = None):
        return self._diagnoses.list_diagnoses(investigation_id)

    # --- Recommendation ---
    def list_recommendations(self) -> Tuple[Dict[str, Any], ...]:
        return self._recommendations

    # --- Summary ---
    def summary(self) -> Dict[str, Any]:
        from datetime import datetime

        return IntelligenceSummary(
            investigation_count=len(self.query_investigations()),
            diagnosis_count=len(self._diagnoses.list_diagnoses()),
            recommendation_count=len(self._recommendations),
            generation_time=datetime.utcnow().isoformat() + "Z",
        ).as_dict()
