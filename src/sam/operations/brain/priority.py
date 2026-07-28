"""
OP-254 — Priority Engine.

Rank recommendations by combining:
  - urgency (how time-sensitive)
  - impact (how bad if ignored)
  - confidence (how sure we are)
  - risk (how risky to ignore)
  - age (how long this has been pending)
  - dependency (how many other issues depend on this)

Output: PriorityScore — a weighted composite score.
"""

from __future__ import annotations

import math
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class PriorityScore:
    """
    Composite priority score for a recommendation.

    score: 0.0 (lowest) to 1.0 (highest priority).
    Each factor contributes 0.0-1.0 independently.
    """

    item_id: str
    score: float
    urgency: float  # 0.0-1.0
    impact: float  # 0.0-1.0
    confidence: float  # 0.0-1.0
    risk: float  # 0.0-1.0
    age: float  # 0.0-1.0
    dependency: float  # 0.0-1.0

    factors: Dict[str, float] = field(default_factory=dict)

    @property
    def label(self) -> str:
        if self.score >= 0.8:
            return "critical"
        elif self.score >= 0.6:
            return "high"
        elif self.score >= 0.4:
            return "medium"
        elif self.score >= 0.2:
            return "low"
        return "trivial"


@dataclass
class PriorityConfig:
    """
    Weight configuration for priority scoring.

    All weights sum to 1.0 by default.
    """

    urgency_weight: float = 0.25
    impact_weight: float = 0.25
    confidence_weight: float = 0.15
    risk_weight: float = 0.15
    age_weight: float = 0.10
    dependency_weight: float = 0.10


# ── Engine ─────────────────────────────────────────────────────────


class PriorityEngine:
    """
    Ranks recommendations by priority.

    Input: list of recommendation dicts (or objects with .priority, .confidence, etc.)
    Output: sorted list of PriorityScore.

    Each recommendation dict should have:
      - id (str)
      - priority (str) — "low", "medium", "high", "critical"
      - confidence (float 0-1)
      - age_seconds (float, optional) — how long since created
      - dependencies (list, optional) — other rec IDs that depend on this
      - affected_count (int, optional) — number of resources affected
      - title (str, optional)
    """

    def __init__(self, config: Optional[PriorityConfig] = None):
        self._config = config or PriorityConfig()
        self._last_scores: List[PriorityScore] = []

    # ── Public API ─────────────────────────────────────────────────

    @property
    def config(self) -> PriorityConfig:
        return self._config

    @config.setter
    def config(self, cfg: PriorityConfig) -> None:
        self._config = cfg

    @property
    def last_scores(self) -> List[PriorityScore]:
        return self._last_scores

    def rank(self, recommendations: List[Dict[str, Any]]) -> List[PriorityScore]:
        """
        Rank recommendations by priority.

        Returns sorted list (highest priority first).
        """
        scores: List[PriorityScore] = []
        max_age = self._find_max_age(recommendations)

        for rec in recommendations:
            score = self._score_one(rec, max_age)
            scores.append(score)

        scores.sort(key=lambda x: x.score, reverse=True)
        self._last_scores = scores
        return scores

    def get_highest(self, recommendations: List[Dict[str, Any]]) -> Optional[PriorityScore]:
        """Get the single highest priority item."""
        scores = self.rank(recommendations)
        return scores[0] if scores else None

    def get_top_n(self, recommendations: List[Dict[str, Any]], n: int = 3) -> List[PriorityScore]:
        """Get top N items."""
        return self.rank(recommendations)[:n]

    def get_critical(self, recommendations: List[Dict[str, Any]]) -> List[PriorityScore]:
        """Get items with score >= 0.8."""
        return [s for s in self.rank(recommendations) if s.score >= 0.8]

    def get_high(self, recommendations: List[Dict[str, Any]]) -> List[PriorityScore]:
        """Get items with score >= 0.6."""
        return [s for s in self.rank(recommendations) if s.score >= 0.6]

    # ── Internal ───────────────────────────────────────────────────

    def _score_one(self, rec: Dict[str, Any], max_age: float) -> PriorityScore:
        item_id = rec.get("id", rec.get("recommendation_id", "unknown"))

        # Urgency: from priority label
        urgency = self._urgency_from_priority(rec.get("priority", "low"))

        # Impact: from affected count (if available), else from priority
        affected = rec.get("affected_count", 0)
        impact = min(1.0, affected / 10.0) if affected else (
            0.9 if rec.get("priority") == "critical" else
            0.7 if rec.get("priority") == "high" else
            0.5 if rec.get("priority") == "medium" else 0.3
        )

        # Confidence: direct
        confidence = min(1.0, max(0.0, rec.get("confidence", 0.5)))

        # Risk: from severity in title/description, else from priority
        risk = self._risk_from_rec(rec)

        # Age: normalize against max
        age = rec.get("age_seconds", 0.0)
        age_factor = min(1.0, age / max_age) if max_age > 0 else 0.0

        # Dependency: count of dependents
        deps = rec.get("dependencies", [])
        dependency = min(1.0, len(deps) / 5.0) if deps else 0.0

        # Weighted composite
        w = self._config
        score = (
            w.urgency_weight * urgency
            + w.impact_weight * impact
            + w.confidence_weight * confidence
            + w.risk_weight * risk
            + w.age_weight * age_factor
            + w.dependency_weight * dependency
        )

        factors = {
            "urgency": urgency,
            "impact": impact,
            "confidence": confidence,
            "risk": risk,
            "age": age_factor,
            "dependency": dependency,
        }

        return PriorityScore(
            item_id=item_id,
            score=round(score, 4),
            urgency=round(urgency, 4),
            impact=round(impact, 4),
            confidence=round(confidence, 4),
            risk=round(risk, 4),
            age=round(age_factor, 4),
            dependency=round(dependency, 4),
            factors=factors,
        )

    def _urgency_from_priority(self, priority: str) -> float:
        mapping = {
            "critical": 1.0,
            "high": 0.8,
            "medium": 0.5,
            "low": 0.2,
            "trivial": 0.0,
        }
        return mapping.get(priority, 0.2)

    def _risk_from_rec(self, rec: Dict[str, Any]) -> float:
        title = (rec.get("title", "") or "").lower()
        desc = (rec.get("description", "") or "").lower()
        combined = title + " " + desc

        risk_keywords = ["failure", "crash", "loss", "deadlock", "stall",
                         "blocked", "timeout", "overflow", "corrupt"]
        found = sum(1 for kw in risk_keywords if kw in combined)
        return min(1.0, found * 0.25)

    def _find_max_age(self, recommendations: List[Dict[str, Any]]) -> float:
        ages = [r.get("age_seconds", 0.0) for r in recommendations]
        return max(ages) if ages else 1.0


# ── Convenience ────────────────────────────────────────────────────


def prioritize(recommendations: List[Dict[str, Any]]) -> List[PriorityScore]:
    """One-shot: rank and return sorted PriorityScore list."""
    engine = PriorityEngine()
    return engine.rank(recommendations)


def build_rec_for_priority(
    rec_id: str,
    priority: str = "medium",
    confidence: float = 0.5,
    age_seconds: float = 0.0,
    affected_count: int = 1,
    dependencies: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Build a recommendation dict compatible with prioritize()."""
    return {
        "id": rec_id,
        "recommendation_id": rec_id,
        "priority": priority,
        "confidence": confidence,
        "age_seconds": age_seconds,
        "affected_count": affected_count,
        "dependencies": dependencies or [],
    }
