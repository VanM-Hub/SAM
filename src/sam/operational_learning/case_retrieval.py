"""Case Retrieval - WP-12 (MISSION-4.3 / IP-4.3-002).

Mendapatkan kembali kasus yang relevan (retrieval berbasis kemiripan).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Optional, Tuple

from .case_repository import Case, CaseRepository
from .similarity_engine import SimilarityEngine, SimilarityScore


@dataclass(frozen=True)
class RetrievedCase:
    """Kasus yang diambil beserta skor kemiripannya."""

    case: Case
    score: SimilarityScore

    def as_dict(self) -> dict:
        return {
            "case": self.case.as_dict(),
            "similarity": self.score.as_dict(),
        }


class CaseRetriever:
    """Mengambil kasus paling relevan untuk query."""

    def __init__(
        self, repository: CaseRepository, engine: Optional[SimilarityEngine] = None
    ) -> None:
        self._repo = repository
        self._engine = engine or SimilarityEngine()

    def retrieve(
        self,
        query: Case,
        *,
        limit: int = 5,
        min_score: float = 0.0,
    ) -> Tuple[RetrievedCase, ...]:
        candidates = self._repo.all()
        scored = self._engine.rank(query, candidates)
        results = []
        for s in scored:
            if s.score < min_score:
                continue
            case = next(
                (c for c in candidates if c.case_id == s.case_id), None
            )
            if case is not None:
                results.append(RetrievedCase(case=case, score=s))
            if len(results) >= limit:
                break
        return tuple(results)
