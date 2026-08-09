"""Learning API - WP-27 (MISSION-4.3 / IP-4.3-003).

Antarmuka untuk continuous learning. API read-only untuk query; feedback
menulis ke store (append-only, bukan mutasi governance).
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any, Dict

from .operational_knowledge import KnowledgeIndex
from .recommendation_feedback import (
    RecommendationFeedback,
    RecommendationFeedbackStore,
)
from .learning_evaluation import LearningEvaluator
from .operational_metrics import LearningMetricsCalculator


@dataclass(frozen=True)
class LearningSummary:
    """Ringkasan status learning."""

    knowledge_count: int = 0
    feedback_count: int = 0
    evaluation: Dict[str, Any] = field(default_factory=dict)
    metrics: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "knowledge_count": self.knowledge_count,
            "feedback_count": self.feedback_count,
            "evaluation": self.evaluation,
            "metrics": self.metrics,
        }


class LearningAPI:
    """Facade untuk continuous learning."""

    def __init__(
        self,
        *,
        knowledge: KnowledgeIndex,
        feedback: RecommendationFeedbackStore,
        experience_count: int = 0,
        case_count: int = 0,
    ) -> None:
        self._knowledge = knowledge
        self._feedback = feedback
        self._experience_count = experience_count
        self._case_count = case_count

    # feedback (write, append-only)
    def submit_feedback(
        self, recommendation_id: str, rating: float, comment: str = ""
    ) -> RecommendationFeedback:
        fb = RecommendationFeedback(
            feedback_id=uuid.uuid4().hex,
            recommendation_id=recommendation_id,
            rating=max(-1.0, min(1.0, rating)),
            comment=comment,
        )
        self._feedback.add(fb)
        return fb

    # read-only queries
    def summary(self) -> Dict[str, Any]:
        feedbacks = self._feedback.all()
        total_rating = sum(f.rating for f in feedbacks)
        evaluation = LearningEvaluator.evaluate(
            "learn-eval",
            knowledge_count=self._knowledge.count(),
            case_count=self._case_count,
            feedback_count=len(feedbacks),
            total_rating=total_rating,
        )
        return LearningSummary(
            knowledge_count=self._knowledge.count(),
            feedback_count=len(feedbacks),
            evaluation=evaluation.as_dict(),
            metrics=LearningMetricsCalculator.calculate(
                total_experiences=self._experience_count,
                total_cases=self._case_count,
                total_knowledge=self._knowledge.count(),
                total_feedback=len(feedbacks),
            ).as_dict(),
        ).as_dict()

    def feedback_count(self) -> int:
        return self._feedback.count()
