"""Recommendation Explainability - WP-26 (MISSION-4.2 / IP-4.2-003).

Menjelaskan dasar rekomendasi beserta evidence & prediction yang
mendukungnya. Evidence chain lengkap, source attribution tersedia.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .evidence_collection import EvidenceModel
from .recommendation_engine import Recommendation
from .consequence_prediction import PredictedConsequence


@dataclass(frozen=True)
class RecommendationExplanation:
    """Penjelasan rekomendasi."""

    recommendation_id: str
    rationale: str
    evidence_chain: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    predicted_consequences: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "rationale": self.rationale,
            "evidence_chain": [list(c) for c in self.evidence_chain],
            "predicted_consequences": list(self.predicted_consequences),
        }


class RecommendationExplainer:
    """Menjelaskan rekomendasi (read-only)."""

    def explain(
        self,
        recommendation: Recommendation,
        evidences: Tuple[EvidenceModel, ...],
        consequences: Tuple[PredictedConsequence, ...] = (),
    ) -> RecommendationExplanation:
        by_id = {e.evidence_id: e for e in evidences}
        chain = tuple(
            (
                eid,
                by_id[eid].source.source_id if eid in by_id else "unknown",
            )
            for eid in recommendation.evidence_ids
        )
        return RecommendationExplanation(
            recommendation_id=recommendation.recommendation_id,
            rationale=recommendation.rationale,
            evidence_chain=chain,
            predicted_consequences=tuple(
                c.as_dict() for c in consequences
            ),
        )
