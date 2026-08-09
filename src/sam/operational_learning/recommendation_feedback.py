"""Recommendation Feedback - WP-21 (MISSION-4.3 / IP-4.3-003).

Menerima & menyimpan feedback atas rekomendasi untuk continuous learning.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Tuple

from .persistent_storage import PersistenceEngine


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class RecommendationFeedback:
    """Feedback atas satu rekomendasi."""

    feedback_id: str
    recommendation_id: str
    rating: float = 0.0  # -1.0 .. 1.0
    comment: str = ""
    outcome: str = ""
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "feedback_id": self.feedback_id,
            "recommendation_id": self.recommendation_id,
            "rating": self.rating,
            "comment": self.comment,
            "outcome": self.outcome,
            "created_at": self.created_at,
        }


class RecommendationFeedbackStore:
    """Penyimpanan feedback (persisten, append-only)."""

    def __init__(self, engine: PersistenceEngine) -> None:
        self._engine = engine

    def add(self, feedback: RecommendationFeedback) -> None:
        self._engine.append(feedback.feedback_id, feedback.as_dict())

    def get(self, feedback_id: str) -> Optional[RecommendationFeedback]:
        rec = self._engine.get(feedback_id)
        if rec is None:
            return None
        p = dict(rec.payload)
        return RecommendationFeedback(
            feedback_id=feedback_id,
            recommendation_id=p.get("recommendation_id", ""),
            rating=p.get("rating", 0.0),
            comment=p.get("comment", ""),
            outcome=p.get("outcome", ""),
            created_at=p.get("created_at", ""),
        )

    def for_recommendation(self, recommendation_id: str) -> Tuple[RecommendationFeedback, ...]:
        result = []
        for rec in self._engine.all():
            p = dict(rec.payload)
            if p.get("recommendation_id") == recommendation_id:
                result.append(
                    RecommendationFeedback(
                        feedback_id=rec.record_id,
                        recommendation_id=p.get("recommendation_id", ""),
                        rating=p.get("rating", 0.0),
                        comment=p.get("comment", ""),
                        outcome=p.get("outcome", ""),
                        created_at=p.get("created_at", ""),
                    )
                )
        return tuple(result)

    def all(self) -> Tuple[RecommendationFeedback, ...]:
        return tuple(self.get(r.record_id) for r in self._engine.all())

    def count(self) -> int:
        return len(self._engine.all())
