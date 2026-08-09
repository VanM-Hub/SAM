"""Learning Evaluation + Experience Verification - WP-23/24 (MISSION-4.3 / IP-4.3-003).

Mengevaluasi kualitas pembelajaran dan memverifikasi pengalaman operasional.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningEvaluation:
    """Evaluasi kualitas pembelajaran."""

    evaluation_id: str
    knowledge_count: int = 0
    case_count: int = 0
    feedback_count: int = 0
    rating: float = 0.0  # -1.0 .. 1.0

    @property
    def is_learning(self) -> bool:
        return self.knowledge_count > 0 and self.feedback_count > 0

    def as_dict(self) -> dict:
        return {
            "evaluation_id": self.evaluation_id,
            "knowledge_count": self.knowledge_count,
            "case_count": self.case_count,
            "feedback_count": self.feedback_count,
            "rating": self.rating,
            "is_learning": self.is_learning,
        }


class LearningEvaluator:
    """Mengevaluasi pembelajaran dari metrik agregat."""

    @staticmethod
    def evaluate(
        evaluation_id: str,
        *,
        knowledge_count: int,
        case_count: int,
        feedback_count: int,
        total_rating: float = 0.0,
    ) -> LearningEvaluation:
        rating = 0.0
        if feedback_count:
            rating = round(total_rating / feedback_count, 3)
        return LearningEvaluation(
            evaluation_id=evaluation_id,
            knowledge_count=knowledge_count,
            case_count=case_count,
            feedback_count=feedback_count,
            rating=rating,
        )


@dataclass(frozen=True)
class VerificationOutcome:
    """Hasil verifikasi pengalaman."""

    experience_id: str
    verified: bool
    method: str = ""
    detail: str = ""

    def as_dict(self) -> dict:
        return {
            "experience_id": self.experience_id,
            "verified": self.verified,
            "method": self.method,
            "detail": self.detail,
        }


class ExperienceVerifier:
    """Memverifikasi pengalaman (immutability & evidence presence)."""

    @staticmethod
    def verify(
        experience_id: str,
        *,
        immutable: bool = True,
        has_evidence: bool = True,
    ) -> VerificationOutcome:
        if not immutable:
            return VerificationOutcome(
                experience_id, False, "immutability", "record modified"
            )
        if not has_evidence:
            return VerificationOutcome(
                experience_id, False, "evidence", "no evidence attached"
            )
        return VerificationOutcome(
            experience_id, True, "integrity", "immutable & evidence-backed"
        )
