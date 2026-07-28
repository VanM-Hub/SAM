"""
OP-262 — Success Estimator.

Menghitung probabilitas sukses suatu rekomendasi atau proposal
berdasarkan 5 faktor tanpa ML/AI:

  1. Historical success rate (dari outcome records)
  2. Similarity score (seberapa mirip dengan case sebelumnya)
  3. Recurrence penalty (apakah rekomendasi pernah gagal sebelumnya)
  4. Evidence quality (berapa banyak dan seberapa kuat evidence)
  5. Risk multiplier (makin tinggi risk, makin rendah estimasi)
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class EvidencePiece:
    """A single piece of evidence."""
    source: str = ""
    type: str = "observation"  # "observation" | "history" | "rule" | "audit"
    value: str = ""
    weight: float = 1.0
    confidence: float = 1.0


@dataclass
class SuccessEstimate:
    """Probability estimate for a recommendation/proposal."""
    recommendation_id: str
    probability: float  # 0.0 - 1.0
    factors: Dict[str, float] = field(default_factory=dict)
    details: Dict[str, Any] = field(default_factory=dict)
    estimated_at: float = 0.0

    def __post_init__(self):
        self.probability = round(max(0.0, min(1.0, self.probability)), 4)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recommendation_id": self.recommendation_id,
            "probability": self.probability,
            "factors": self.factors,
            "details": self.details,
        }


@dataclass
class EstimatorConfig:
    """Configuration for success estimation."""
    history_weight: float = 0.30
    similarity_weight: float = 0.20
    recurrence_penalty: float = 0.15
    evidence_weight: float = 0.20
    risk_weight: float = 0.15
    min_records_for_history: int = 3
    default_unknown_probability: float = 0.65


@dataclass
class HistoricalOutcome:
    """A historical outcome record."""
    record_id: str
    source_type: str  # "recommendation" | "proposal"
    title: str = ""
    success: bool = False
    similarity_score: float = 0.0
    timestamp: float = 0.0


# ── Engine ─────────────────────────────────────────────────────────


class SuccessEstimator:
    """
    Estimate success probability for recommendations/proposals.

    All factors are deterministic and evidence-based.
    No ML/AI dependencies.
    """

    def __init__(self, config: Optional[EstimatorConfig] = None):
        self.config = config or EstimatorConfig()
        self._history: List[HistoricalOutcome] = []
        self._last_estimate: Optional[SuccessEstimate] = None

    @property
    def last_estimate(self) -> Optional[SuccessEstimate]:
        return self._last_estimate

    @property
    def history(self) -> List[HistoricalOutcome]:
        return list(self._history)

    def add_outcome(self, outcome: HistoricalOutcome) -> None:
        """Add a historical outcome record."""
        self._history.append(outcome)

    def add_outcomes(self, outcomes: List[HistoricalOutcome]) -> None:
        """Add multiple outcomes."""
        self._history.extend(outcomes)

    def estimate(
        self,
        recommendation_id: str,
        title: str = "",
        evidence: Optional[List[EvidencePiece]] = None,
        risk_score: float = 0.5,
        source_type: str = "recommendation",
    ) -> SuccessEstimate:
        """
        Estimate success probability.

        Args:
          recommendation_id: Unique ID
          title: Recommendation title (for similarity matching)
          evidence: List of supporting evidence
          risk_score: 0.0 (no risk) to 1.0 (max risk)
          source_type: "recommendation" or "proposal"

        Returns: SuccessEstimate with probability 0.0-1.0
        """
        evidence = evidence or []

        # 1. Historical success rate
        hist_score = self._calc_historical_score(recommendation_id, title)

        # 2. Similarity to past successes
        sim_score = self._calc_similarity_score(title)

        # 3. Recurrence penalty
        rec_penalty = self._calc_recurrence_penalty(recommendation_id, title)

        # 4. Evidence quality
        ev_score = self._calc_evidence_quality(evidence)

        # 5. Risk multiplier
        risk_factor = 1.0 - risk_score

        # Combine
        c = self.config
        probability = (
            hist_score * c.history_weight +
            sim_score * c.similarity_weight +
            (1.0 - rec_penalty) * c.recurrence_penalty +
            ev_score * c.evidence_weight +
            risk_factor * c.risk_weight
        )

        # Clamp
        probability = max(0.05, min(0.99, probability))

        estimate = SuccessEstimate(
            recommendation_id=recommendation_id,
            probability=round(probability, 4),
            factors={
                "historical_rate": round(hist_score, 4),
                "similarity_score": round(sim_score, 4),
                "recurrence_penalty": round(rec_penalty, 4),
                "evidence_quality": round(ev_score, 4),
                "risk_factor": round(risk_factor, 4),
            },
            details={
                "title": title,
                "source_type": source_type,
                "history_count": len(self._history),
                "evidence_count": len(evidence),
                "risk_score": risk_score,
                "config_weights": {
                    "history": c.history_weight,
                    "similarity": c.similarity_weight,
                    "recurrence": c.recurrence_penalty,
                    "evidence": c.evidence_weight,
                    "risk": c.risk_weight,
                },
            },
            estimated_at=time.time(),
        )
        self._last_estimate = estimate
        return estimate

    # ── Factor calculators ─────────────────────────────────────────

    def _calc_historical_score(
        self, rec_id: str, title: str
    ) -> float:
        """Calculate success rate from history."""
        if len(self._history) < self.config.min_records_for_history:
            return self.config.default_unknown_probability

        # Match by ID first
        exact = [
            h for h in self._history
            if h.record_id == rec_id
        ]
        if exact:
            successes = sum(1 for h in exact if h.success)
            return successes / len(exact)

        # Match by title keywords
        if title:
            keywords = title.lower().split()
            similar = [
                h for h in self._history
                if any(kw in h.title.lower() for kw in keywords)
            ]
            if len(similar) >= self.config.min_records_for_history:
                successes = sum(1 for h in similar if h.success)
                return successes / len(similar)

        return self.config.default_unknown_probability

    def _calc_similarity_score(self, title: str) -> float:
        """Calculate how similar this rec is to past successes."""
        if not self._history:
            return self.config.default_unknown_probability

        if not title:
            return 0.5

        keywords = set(title.lower().split())
        if not keywords:
            return 0.5

        successes = [h for h in self._history if h.success]
        if not successes:
            return 0.4

        scores = []
        for h in successes:
            h_keywords = set(h.title.lower().split())
            overlap = len(keywords & h_keywords)
            total = len(keywords | h_keywords)
            similarity = overlap / total if total > 0 else 0
            scores.append(similarity)

        return sum(scores) / len(scores) if scores else 0.5

    def _calc_recurrence_penalty(self, rec_id: str, title: str) -> float:
        """Calculate penalty for repeated failures."""
        matches = [
            h for h in self._history
            if h.record_id == rec_id
        ]
        if not matches:
            return 0.0

        failures = [h for h in matches if not h.success]
        return len(failures) / len(matches) if matches else 0.0

    def _calc_evidence_quality(self, evidence: List[EvidencePiece]) -> float:
        """Calculate evidence quality score."""
        if not evidence:
            return 0.3

        total_weight = 0.0
        weighted_confidence = 0.0

        for ev in evidence:
            total_weight += ev.weight
            weighted_confidence += ev.weight * ev.confidence

        if total_weight <= 0:
            return 0.3

        base_score = weighted_confidence / total_weight

        # Bonus for variety of sources
        sources = set(ev.source for ev in evidence if ev.source)
        source_bonus = min(0.15, len(sources) * 0.05)

        return min(1.0, base_score + source_bonus)


# ── Convenience ────────────────────────────────────────────────────


def estimate_success(
    recommendation_id: str,
    title: str = "",
    evidence: Optional[List[EvidencePiece]] = None,
    risk_score: float = 0.5,
    outcomes: Optional[List[HistoricalOutcome]] = None,
) -> SuccessEstimate:
    """One-shot: estimate success probability."""
    estimator = SuccessEstimator()
    if outcomes:
        estimator.add_outcomes(outcomes)
    return estimator.estimate(recommendation_id, title, evidence, risk_score)
