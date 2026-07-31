"""Memory Score — skor memori (Sprint 178).

7 dimensi: Structure, Integrity, Consistency, Completeness,
Determinism, Immutability, PreviewOnly.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class MemoryScoreDimension:
    """Dimensi skor (immutable)."""
    name: str
    score: float = 0.0
    max_score: float = 100.0


@dataclass(frozen=True)
class MemoryScore:
    """Skor memori (immutable)."""
    total: float = 0.0
    dimensions: List[MemoryScoreDimension] = field(default_factory=list)


class MemoryScorer:
    """Scorer memori. Deterministik."""

    def compute(self, criteria) -> float:
        if not criteria:
            return 0.0
        passed = sum(1 for c in criteria if c.passed)
        return (passed / len(criteria)) * 100.0

    def dimension_scores(self, criteria) -> List[MemoryScoreDimension]:
        per = 100.0 / len(criteria) if criteria else 0
        return [
            MemoryScoreDimension(name=c.name, score=per if c.passed else 0.0)
            for c in criteria
        ]
