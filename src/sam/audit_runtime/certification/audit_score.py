"""Audit Score — skor sertifikasi audit (Sprint 218).

Tanpa import silang dari audit_certification untuk menghindari siklus.
Menggunakan duck typing pada objek kriteria (membaca atribut .passed/.name).
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List


@dataclass(frozen=True)
class AuditScoreDimension:
    """Dimensi skor immutable."""
    name: str
    score: float = 0.0
    max_score: float = 100.0


@dataclass(frozen=True)
class AuditScore:
    """Skor immutable."""
    total: float = 0.0


class PolicyScorer:
    """Skor sertifikasi. Read-only deterministik (duck typing)."""

    @staticmethod
    def compute(criteria) -> float:
        if not criteria:
            return 0.0
        return sum(1 for c in criteria if c.passed) / len(criteria) * 100.0

    @staticmethod
    def dimension_scores(criteria) -> List[AuditScoreDimension]:
        return [AuditScoreDimension(c.name, 100.0 if c.passed else 0.0)
                for c in criteria]
