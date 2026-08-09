"""Operational Metrics - WP-26 (MISSION-4.3 / IP-4.3-003).

Menghitung metrik operasional pembelajaran (deterministik).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class LearningMetrics:
    """Metrik pembelajaran operasional."""

    total_experiences: int = 0
    total_cases: int = 0
    total_knowledge: int = 0
    total_feedback: int = 0
    learning_rate: float = 0.0
    validation_rate: float = 0.0

    def as_dict(self) -> dict:
        return {
            "total_experiences": self.total_experiences,
            "total_cases": self.total_cases,
            "total_knowledge": self.total_knowledge,
            "total_feedback": self.total_feedback,
            "learning_rate": self.learning_rate,
            "validation_rate": self.validation_rate,
        }


class LearningMetricsCalculator:
    """Menghitung metrik dari komponen pembelajaran."""

    @staticmethod
    def calculate(
        *,
        total_experiences: int = 0,
        total_cases: int = 0,
        total_knowledge: int = 0,
        total_feedback: int = 0,
        validated_knowledge: int = 0,
    ) -> LearningMetrics:
        learning_rate = 0.0
        if total_experiences:
            learning_rate = round(total_knowledge / total_experiences, 3)
        validation_rate = 0.0
        if total_knowledge:
            validation_rate = round(validated_knowledge / total_knowledge, 3)
        return LearningMetrics(
            total_experiences=total_experiences,
            total_cases=total_cases,
            total_knowledge=total_knowledge,
            total_feedback=total_feedback,
            learning_rate=learning_rate,
            validation_rate=validation_rate,
        )
