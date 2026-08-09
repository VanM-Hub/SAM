"""Risk Evaluation - WP-25 (MISSION-4.2 / IP-4.2-003).

Mengevaluasi risiko tindakan yang direkomendasikan (deterministik).
Read-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class RiskFactor:
    """Satu faktor risiko."""

    name: str
    likelihood: float = 0.0
    impact: str = "low"  # low | medium | high
    mitigation: str = ""

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "likelihood": self.likelihood,
            "impact": self.impact,
            "mitigation": self.mitigation,
        }


@dataclass(frozen=True)
class RiskEvaluation:
    """Hasil evaluasi risiko."""

    evaluation_id: str
    factors: Tuple[RiskFactor, ...] = field(default_factory=tuple)
    overall_risk: float = 0.0

    @property
    def level(self) -> str:
        if self.overall_risk >= 0.7:
            return "high"
        if self.overall_risk >= 0.4:
            return "medium"
        if self.overall_risk > 0.0:
            return "low"
        return "none"

    def as_dict(self) -> dict:
        return {
            "evaluation_id": self.evaluation_id,
            "factors": [f.as_dict() for f in self.factors],
            "overall_risk": self.overall_risk,
            "level": self.level,
        }


class RiskEvaluator:
    """Mengevaluasi risiko agregat (deterministik)."""

    @staticmethod
    def _impact_value(impact: str) -> float:
        return {"low": 0.3, "medium": 0.6, "high": 1.0}.get(impact, 0.3)

    def evaluate(self, evaluation_id: str, factors) -> RiskEvaluation:
        factors = tuple(factors)
        if not factors:
            return RiskEvaluation(evaluation_id=evaluation_id)
        overall = round(
            sum(
                min(1.0, f.likelihood * self._impact_value(f.impact))
                for f in factors
            )
            / len(factors),
            3,
        )
        return RiskEvaluation(
            evaluation_id=evaluation_id,
            factors=factors,
            overall_risk=overall,
        )
