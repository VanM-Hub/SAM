"""Recommendation Engine - WP-23 (MISSION-4.2 / IP-4.2-003).

Menyusun rekomendasi berbasis evidence sebelum eksekusi.
Read-only, deterministik, evidence-backed.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Tuple

from .evidence_collection import EvidenceModel
from .operational_diagnosis import OperationalDiagnosis


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class Recommendation:
    """Satu rekomendasi operasional."""

    recommendation_id: str
    action: str
    rationale: str
    priority: str = "normal"  # high | medium | low
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "action": self.action,
            "rationale": self.rationale,
            "priority": self.priority,
            "evidence_ids": list(self.evidence_ids),
            "created_at": self.created_at,
        }


@dataclass(frozen=True)
class RecommendationResult:
    """Kumpulan rekomendasi untuk sebuah diagnosis."""

    diagnosis: Dict[str, Any]
    recommendations: Tuple[Recommendation, ...] = field(default_factory=tuple)

    @property
    def recommendation_count(self) -> int:
        return len(self.recommendations)

    def as_dict(self) -> dict:
        return {
            "diagnosis": self.diagnosis,
            "recommendations": [r.as_dict() for r in self.recommendations],
            "recommendation_count": self.recommendation_count,
        }


class EvidenceBasedRecommendationEngine:
    """Rekomendasi berbasis evidence."""

    def recommend(
        self,
        diagnosis: OperationalDiagnosis,
        evidences: Tuple[EvidenceModel, ...],
    ) -> RecommendationResult:
        evidence_ids = tuple(
            dict.fromkeys(diagnosis.evidence_ids)
        )
        action = self._derive_action(diagnosis.root_cause)
        rec = Recommendation(
            recommendation_id=f"rec-{diagnosis.diagnosis_id[:8]}",
            action=action,
            rationale=(
                f"Based on diagnosis: {diagnosis.root_cause} "
                f"(confidence {diagnosis.confidence.level})."
            ),
            priority=self._derive_priority(diagnosis.confidence.value),
            evidence_ids=evidence_ids,
        )
        return RecommendationResult(
            diagnosis=diagnosis.as_dict(),
            recommendations=(rec,),
        )

    @staticmethod
    def _derive_action(root_cause: str) -> str:
        text = root_cause.lower()
        if "provider" in text:
            return "Investigate and restore provider availability"
        if "runtime" in text or "resource" in text:
            return "Review runtime resource allocation"
        return "Validate root cause and plan corrective action"

    @staticmethod
    def _derive_priority(confidence: float) -> str:
        if confidence >= 0.8:
            return "high"
        if confidence >= 0.5:
            return "medium"
        return "low"
