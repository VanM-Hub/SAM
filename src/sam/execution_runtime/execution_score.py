"""Execution Score (Sprint 258).

Program C - Real Execution Runtime.
Skor immutable satu dimensi sertifikasi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List


@dataclass(frozen=True)
class ExecutionScore:
    """Skor satu dimensi (immutable)."""
    dimension: str
    score: float
    passed: bool
    details: str = ""

    def as_dict(self) -> dict:
        return {"dimension": self.dimension, "score": self.score,
                "passed": self.passed, "details": self.details}


@dataclass(frozen=True)
class ExecutionScoreSet:
    """Kumpulan skor (immutable)."""
    scores: dict = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {k: v.as_dict() for k, v in self.scores.items()}

    def all_passed(self) -> bool:
        return all(s.passed for s in self.scores.values())
