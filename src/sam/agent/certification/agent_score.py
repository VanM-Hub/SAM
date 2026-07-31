"""Agent Score — skor agent (Sprint 163).

Score dimensions (blueprint):
Completeness, Consistency, Determinism, Layer Safety,
Architecture Safety, DTO Safety, Pipeline Safety.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class ScoreDimension:
    """Dimensi skor (immutable)."""
    name: str
    score: float = 0.0
    max_score: float = 100.0


@dataclass(frozen=True)
class AgentScore:
    """Skor agent (immutable)."""
    total: float = 0.0
    dimensions: List[ScoreDimension] = field(default_factory=list)


class AgentScorer:
    """Scorer agent. Deterministik."""

    def compute(self, criteria: List[CertificationCriterion]) -> float:
        if not criteria:
            return 0.0
        passed = sum(1 for c in criteria if c.passed)
        return (passed / len(criteria)) * 100.0

    def dimension_scores(self, criteria: List[CertificationCriterion]) -> List[ScoreDimension]:
        per = 100.0 / len(criteria) if criteria else 0
        return [
            ScoreDimension(name=c.name, score=per if c.passed else 0.0)
            for c in criteria
        ]


__all__ = ["AgentScorer", "AgentScore", "ScoreDimension"]
