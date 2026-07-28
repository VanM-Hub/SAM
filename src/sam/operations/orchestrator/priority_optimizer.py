"""
OP-273 — Priority Optimizer

Input: Recommendation, Trust, Severity, Confidence, Dependency, Age, Risk
Output: PriorityPlan (rekomendasi urutan — bukan Priority Queue)

Hanya memberikan rekomendasi urutan prioritas berdasarkan
multi-variable scoring. Tidak submit mission, tidak auto-execute.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class PriorityItem:
    proposal_id: str
    score: float
    rank: int
    factors: dict[str, float] = field(default_factory=dict)
    reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "proposal_id": self.proposal_id,
            "score": self.score,
            "rank": self.rank,
            "factors": self.factors,
            "reason": self.reason,
        }


@dataclass(frozen=True)
class PriorityPlan:
    items: tuple[PriorityItem, ...]
    total_items: int = 0
    highest_score: float = 0.0
    lowest_score: float = 0.0
    average_score: float = 0.0

    @property
    def ordered_ids(self) -> list[str]:
        return [i.proposal_id for i in self.items]

    def by_proposal_id(self, proposal_id: str) -> PriorityItem | None:
        for item in self.items:
            if item.proposal_id == proposal_id:
                return item
        return None

    def to_dict(self) -> dict[str, Any]:
        return {
            "total_items": self.total_items,
            "highest_score": self.highest_score,
            "lowest_score": self.lowest_score,
            "average_score": self.average_score,
            "items": [i.to_dict() for i in self.items],
            "ordered_ids": self.ordered_ids,
        }


class PriorityOptimizer:
    """
    Menghitung skor prioritas untuk proposal berdasarkan:
      - recommendation score (0-100)
      - trust score (0-100)
      - severity weight
      - confidence (0-1)
      - dependency count (lebih banyak = lebih prioritas)
      - age (semakin lama = semakin prioritas)
      - risk score (0-100)
    """

    # Bobot default
    WEIGHT_RECOMMENDATION: float = 0.25
    WEIGHT_TRUST: float = 0.15
    WEIGHT_SEVERITY: float = 0.20
    WEIGHT_CONFIDENCE: float = 0.10
    WEIGHT_DEPENDENCY: float = 0.10
    WEIGHT_AGE: float = 0.05
    WEIGHT_RISK: float = 0.15

    def __init__(self,
                 w_recommendation: float | None = None,
                 w_trust: float | None = None,
                 w_severity: float | None = None,
                 w_confidence: float | None = None,
                 w_dependency: float | None = None,
                 w_age: float | None = None,
                 w_risk: float | None = None,
                 ) -> None:
        self._w_rec = w_recommendation or self.WEIGHT_RECOMMENDATION
        self._w_trust = w_trust or self.WEIGHT_TRUST
        self._w_sev = w_severity or self.WEIGHT_SEVERITY
        self._w_conf = w_confidence or self.WEIGHT_CONFIDENCE
        self._w_dep = w_dependency or self.WEIGHT_DEPENDENCY
        self._w_age = w_age or self.WEIGHT_AGE
        self._w_risk = w_risk or self.WEIGHT_RISK

    def optimize(self, proposals: list[dict[str, Any]]) -> PriorityPlan:
        """
        Calculate priority scores and rank proposals.

        Each proposal dict may contain:
          - id (required)
          - recommendation_score (0-100)
          - trust_score (0-100)
          - severity (str): critical, high, medium, low, info
          - confidence (0-1)
          - depends_on (list[str])
          - age_hours (float)
          - risk_score (0-100)
        """
        scored: list[tuple[float, dict[str, Any], dict[str, float]]] = []

        for p in proposals:
            pid = p["id"]
            factors: dict[str, float] = {}

            # Recommendation score (0-100)
            rec = float(p.get("recommendation_score", 50))
            factors["recommendation"] = round(rec * self._w_rec, 2)

            # Trust score (0-100)
            trust = float(p.get("trust_score", 50))
            factors["trust"] = round(trust * self._w_trust, 2)

            # Severity weight
            severity_map = {
                "critical": 100, "high": 75, "medium": 50,
                "low": 25, "info": 10,
            }
            sev = float(severity_map.get(p.get("severity", "").lower(), 25))
            factors["severity"] = round(sev * self._w_sev, 2)

            # Confidence (0-1 mapped to 0-100)
            conf = float(p.get("confidence", 0.5)) * 100
            factors["confidence"] = round(conf * self._w_conf, 2)

            # Dependency count (more = more priority)
            deps = p.get("depends_on", [])
            dep_score = min(len(deps) * 20, 100)
            factors["dependency"] = round(dep_score * self._w_dep, 2)

            # Age (hours, older = higher priority)
            age = float(p.get("age_hours", 0))
            age_score = min(age * 5, 100)
            factors["age"] = round(age_score * self._w_age, 2)

            # Risk score (0-100)
            risk = float(p.get("risk_score", 0))
            factors["risk"] = round(risk * self._w_risk, 2)

            total = round(sum(factors.values()), 2)
            scored.append((total, p, factors))

        # Sort descending by total score
        scored.sort(key=lambda x: -x[0])

        items: list[PriorityItem] = []
        for rank, (total, p, factors) in enumerate(scored, 1):
            # Generate reason
            top_factor = max(factors, key=factors.get)
            reason = (f"Score {total}: highest factor = {top_factor} "
                      f"({factors[top_factor]:.1f})")

            items.append(PriorityItem(
                proposal_id=p["id"],
                score=total,
                rank=rank,
                factors=factors,
                reason=reason,
            ))

        scores = [i.score for i in items]
        return PriorityPlan(
            items=tuple(items),
            total_items=len(items),
            highest_score=max(scores) if scores else 0.0,
            lowest_score=min(scores) if scores else 0.0,
            average_score=round(sum(scores) / len(scores), 2) if scores else 0.0,
        )
