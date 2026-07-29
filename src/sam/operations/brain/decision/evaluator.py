"""
OP-303 — Decision Evaluator

Evaluasi keputusan berdasarkan ReasoningResponse, EvidenceSet, dan DecisionContext.
Rule-based. Tidak ada AI. Tidak memanggil penyedia layanan.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class EvidenceItem:
    evidence_id: str = ""
    content: str = ""
    source: str = ""
    relevance: float = 0.5  # 0.0 - 1.0

    def to_dict(self) -> Dict[str, Any]:
        return {"evidence_id": self.evidence_id, "content": self.content[:100], "source": self.source, "relevance": self.relevance}


@dataclass(frozen=True)
class EvidenceSet:
    items: Tuple[EvidenceItem, ...] = ()
    total_items: int = 0
    average_relevance: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "items": [i.to_dict() for i in self.items],
            "total_items": self.total_items,
            "average_relevance": self.average_relevance,
        }


@dataclass(frozen=True)
class DecisionEvaluation:
    score: float  # 0.0 - 1.0 overall
    confidence: float
    evidence_coverage: float
    operational_impact: str  # low, medium, high, critical
    urgency: str  # low, medium, high, immediate
    reversibility: str  # fully_reversible, reversible, hard_to_reverse, irreversible
    risk_level: str  # low, medium, high, critical
    recommendation_quality: float
    evaluation_detail: Tuple[str, ...] = ()
    evaluated_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "score": self.score,
            "confidence": self.confidence,
            "evidence_coverage": self.evidence_coverage,
            "operational_impact": self.operational_impact,
            "urgency": self.urgency,
            "reversibility": self.reversibility,
            "risk_level": self.risk_level,
            "recommendation_quality": self.recommendation_quality,
            "evaluation_detail": list(self.evaluation_detail),
            "evaluated_at": self.evaluated_at,
        }


class DecisionEvaluator:
    """
    Rule-based evaluator.
    Tidak ada AI. Tidak memanggil penyedia.
    """

    # ── Impact thresholds ─────────────────────────────────────────

    IMPACT_THRESHOLDS = [("critical", 0.8), ("high", 0.6), ("medium", 0.3), ("low", 0.0)]
    URGENCY_THRESHOLDS = [("immediate", 0.8), ("high", 0.6), ("medium", 0.3), ("low", 0.0)]
    REVERSIBILITY_THRESHOLDS = [("irreversible", 0.8), ("hard_to_reverse", 0.6), ("reversible", 0.3), ("fully_reversible", 0.0)]
    RISK_THRESHOLDS = [("critical", 0.8), ("high", 0.6), ("medium", 0.3), ("low", 0.0)]

    def evaluate(
        self,
        response: Any,
        evidence_set: Optional[EvidenceSet] = None,
        context: Any = None,
        reasoning_confidence: float = 0.0,
        reasoning_evidence_ids: Optional[Tuple[str, ...]] = None,
        reasoning_latency_ms: float = 0.0,
        reasoning_attempts: int = 1,
        supported_claims: int = 0,
        total_claims: int = 1,
        recommendation_summary: str = "",
    ) -> DecisionEvaluation:
        detail: list[str] = []

        # 1. Confidence
        confidence = self._evaluate_confidence(reasoning_confidence, total_claims, supported_claims)
        if confidence < 0.5:
            detail.append("Low confidence: insufficient supporting evidence")

        # 2. Evidence coverage
        ev = evidence_set or EvidenceSet()
        evidence_coverage = self._evaluate_coverage(
            ev, reasoning_evidence_ids or (), total_claims
        )
        if evidence_coverage < 0.3:
            detail.append("Low evidence coverage: majority of claims unsupported")

        # 3. Operational impact
        impact_score = self._compute_impact_score(context, ev)
        operational_impact = self._classify(impact_score, self.IMPACT_THRESHOLDS)
        if operational_impact == "critical":
            detail.append("Critical operational impact detected")

        # 4. Urgency
        urgency_score = self._compute_urgency_score(context, recommendation_summary)
        urgency = self._classify(urgency_score, self.URGENCY_THRESHOLDS)
        if urgency == "immediate":
            detail.append("Immediate urgency: requires prompt action")

        # 5. Reversibility
        reversibility_score = self._compute_reversibility_score(recommendation_summary)
        reversibility = self._classify(reversibility_score, self.REVERSIBILITY_THRESHOLDS)
        if reversibility == "irreversible":
            detail.append("Irreversible decision: maximum caution required")

        # 6. Risk
        risk_score = self._compute_risk_score(impact_score, urgency_score, reversibility_score, evidence_coverage)
        risk_level = self._classify(risk_score, self.RISK_THRESHOLDS)
        if risk_level != "low":
            detail.append(f"Risk level: {risk_level}")

        # 7. Recommendation quality
        rec_quality = self._compute_rec_quality(confidence, evidence_coverage, risk_score)

        # 8. Overall score
        weights = {"confidence": 0.2, "coverage": 0.25, "rec_quality": 0.25, "risk_inverse": 0.3}
        risk_inverse = 1.0 - risk_score
        score = (
            weights["confidence"] * confidence
            + weights["coverage"] * evidence_coverage
            + weights["rec_quality"] * rec_quality
            + weights["risk_inverse"] * risk_inverse
        )
        score = round(max(0.0, min(1.0, score)), 2)

        return DecisionEvaluation(
            score=score,
            confidence=round(confidence, 2),
            evidence_coverage=round(evidence_coverage, 2),
            operational_impact=operational_impact,
            urgency=urgency,
            reversibility=reversibility,
            risk_level=risk_level,
            recommendation_quality=round(rec_quality, 2),
            evaluation_detail=tuple(detail),
            evaluated_at=datetime.now().isoformat(timespec="seconds"),
        )

    def _evaluate_confidence(self, confidence: float, total: int, supported: int) -> float:
        if total == 0:
            return confidence
        support_ratio = supported / total
        return confidence * 0.4 + support_ratio * 0.6

    def _evaluate_coverage(self, ev: EvidenceSet, evidence_ids: Tuple[str, ...], claims: int) -> float:
        if claims == 0:
            return 1.0
        evidence_count = max(len(evidence_ids), ev.total_items)
        coverage = evidence_count / max(claims, 1)
        relevance_bonus = ev.average_relevance * 0.2
        return min(1.0, coverage + relevance_bonus)

    def _compute_impact_score(self, context: Any, ev: EvidenceSet) -> float:
        # Default based on evidence volume and critical findings
        score = 0.2
        if ev.total_items > 5:
            score += 0.1
        if ev.total_items > 10:
            score += 0.1
        avg_relevance = ev.average_relevance
        score += avg_relevance * 0.3
        if context and hasattr(context, "findings"):
            crit = getattr(context.findings, "critical_findings", 0)
            score += min(crit * 0.05, 0.2)
        return min(1.0, score)

    def _compute_urgency_score(self, context: Any, summary: str) -> float:
        score = 0.1
        urgent_keywords = ["immediate", "urgent", "critical", "asap", "now", "failing", "down", "blocked"]
        if summary:
            lower = summary.lower()
            for kw in urgent_keywords:
                if kw in lower:
                    score += 0.15
        if context and hasattr(context, "health"):
            h = getattr(context, "health", None)
            if h and hasattr(h, "alerts"):
                score += min(len(h.alerts) * 0.05, 0.2)
        return min(1.0, score)

    def _compute_reversibility_score(self, summary: str) -> float:
        score = 0.2
        irreversible_keywords = ["delete", "remove", "permanent", "irreversible", "destroy", "terminate"]
        if summary:
            lower = summary.lower()
            for kw in irreversible_keywords:
                if kw in lower:
                    score += 0.15
        return min(1.0, score)

    def _compute_risk_score(self, impact: float, urgency: float, reversibility: float, coverage: float) -> float:
        return round(
            impact * 0.3 + urgency * 0.2 + reversibility * 0.2 + (1.0 - coverage) * 0.3,
            2,
        )

    def _compute_rec_quality(self, confidence: float, coverage: float, risk: float) -> float:
        return round(confidence * 0.4 + coverage * 0.4 + (1.0 - risk) * 0.2, 2)

    def _classify(self, score: float, thresholds: List[Tuple[str, float]]) -> str:
        for label, thresh in thresholds:
            if score >= thresh:
                return label
        return thresholds[-1][0]
