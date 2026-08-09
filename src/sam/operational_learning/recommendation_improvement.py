"""Recommendation Improvement - WP-22 (MISSION-4.3 / IP-4.3-002).

Meningkatkan kualitas rekomendasi berdasarkan feedback & pengalaman
sebelumnya (deterministik).
"""
from __future__ import annotations

from dataclasses import dataclass

from .recommendation_feedback import RecommendationFeedbackStore


@dataclass(frozen=True)
class RecommendationAdjustment:
    """Penyesuaian rekomendasi berdasarkan learning."""

    recommendation_id: str
    original_priority: str
    adjusted_priority: str
    adjustment: float  # delta -1.0 .. 1.0
    feedback_samples: int = 0

    def as_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "original_priority": self.original_priority,
            "adjusted_priority": self.adjusted_priority,
            "adjustment": self.adjustment,
            "feedback_samples": self.feedback_samples,
        }


class RecommendationImprover:
    """Menyesuaikan prioritas rekomendasi dari feedback agregat."""

    PRIORITY_RANK = {"low": 0, "normal": 1, "medium": 1, "high": 2}

    def __init__(self, store: RecommendationFeedbackStore) -> None:
        self._store = store

    def improve(
        self, recommendation_id: str, current_priority: str
    ) -> RecommendationAdjustment:
        feedbacks = self._store.for_recommendation(recommendation_id)
        if not feedbacks:
            return RecommendationAdjustment(
                recommendation_id=recommendation_id,
                original_priority=current_priority,
                adjusted_priority=current_priority,
                adjustment=0.0,
                feedback_samples=0,
            )
        avg_rating = sum(f.rating for f in feedbacks) / len(feedbacks)
        # rating positif -> naik prioritas; negatif -> turun
        step = 1 if avg_rating > 0.15 else (-1 if avg_rating < -0.15 else 0)
        rank = self.PRIORITY_RANK.get(current_priority, 1)
        new_rank = max(0, min(2, rank + step))
        adjusted = {
            0: "low",
            1: "normal",
            2: "high",
        }[new_rank]
        return RecommendationAdjustment(
            recommendation_id=recommendation_id,
            original_priority=current_priority,
            adjusted_priority=adjusted,
            adjustment=avg_rating,
            feedback_samples=len(feedbacks),
        )
