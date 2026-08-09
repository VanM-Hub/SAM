"""Similarity Engine - WP-13 (MISSION-4.3 / IP-4.3-002).

Menghitung kemiripan antar kasus (deterministik, berbasis fitur).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Tuple

from .case_repository import Case


@dataclass(frozen=True)
class SimilarityScore:
    """Skor kemiripan satu pasangan kasus."""

    case_id: str
    score: float  # 0.0 - 1.0
    matched_features: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "case_id": self.case_id,
            "score": self.score,
            "matched_features": list(self.matched_features),
        }


class SimilarityEngine:
    """Menghitung kemiripan kasus berdasarkan kesamaan fitur."""

    @staticmethod
    def similarity(a: Case, b: Case) -> SimilarityScore:
        fa = a.feature_dict()
        fb = b.feature_dict()
        keys = set(fa.keys()) | set(fb.keys())
        if not keys:
            return SimilarityScore(case_id=b.case_id, score=0.0)
        matched: List[str] = []
        for key in keys:
            if key in fa and key in fb and fa[key] == fb[key]:
                matched.append(key)
        score = round(len(matched) / len(keys), 3)
        return SimilarityScore(
            case_id=b.case_id, score=score, matched_features=tuple(matched)
        )

    def rank(self, query: Case, candidates: Tuple[Case, ...]) -> Tuple[SimilarityScore, ...]:
        scored = [self.similarity(query, c) for c in candidates]
        scored.sort(key=lambda s: s.score, reverse=True)
        return tuple(scored)
