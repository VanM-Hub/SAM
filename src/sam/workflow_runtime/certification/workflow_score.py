"""Workflow Score — skor workflow (Sprint 202)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class WorkflowScoreDimension:
    """Dimensi skor (immutable)."""
    name: str
    score: float = 0.0
    max_score: float = 100.0


@dataclass(frozen=True)
class WorkflowScore:
    """Skor workflow (immutable)."""
    total: float = 0.0
    dimensions: List[WorkflowScoreDimension] = field(default_factory=list)


class WorkflowScorer:
    """Scorer workflow. Deterministik."""

    def compute(self, criteria) -> float:
        if not criteria:
            return 0.0
        passed = sum(1 for c in criteria if c.passed)
        return (passed / len(criteria)) * 100.0

    def dimension_scores(self, criteria) -> List[WorkflowScoreDimension]:
        per = 100.0 / len(criteria) if criteria else 0
        return [
            WorkflowScoreDimension(name=c.name, score=per if c.passed else 0.0)
            for c in criteria
        ]
