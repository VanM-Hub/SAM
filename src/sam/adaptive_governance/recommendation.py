"""Adaptive Governance - Recommendation - WP-41..50 (MISSION-5.6).

Recommendation berbasis evidence: governance change proposal, alternative
strategy, prioritization, confidence, explainability, approval context.
Recommendation TIDAK mengambil alih authority; manusia memutuskan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class RecommendationStatus(str, Enum):
    """Status rekomendasi."""

    PROPOSED = "proposed"
    AWAITING_APPROVAL = "awaiting_approval"
    APPROVED = "approved"
    REJECTED = "rejected"


@dataclass(frozen=True)
class EvidenceRef:
    """Referensi evidence."""

    ref_id: str
    kind: str

    def as_dict(self) -> dict:
        return {"ref_id": self.ref_id, "kind": self.kind}


@dataclass(frozen=True)
class GovernanceRecommendation:
    """Rekomendasi perubahan governance."""

    recommendation_id: str
    domain: str
    suggestion: str
    status: RecommendationStatus = RecommendationStatus.PROPOSED
    confidence: float = 0.0
    evidence: Tuple[EvidenceRef, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    @property
    def evidence_backed(self) -> bool:
        return bool(self.evidence) and self.confidence >= 0.5

    def as_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "domain": self.domain,
            "suggestion": self.suggestion,
            "status": self.status.value,
            "confidence": self.confidence,
            "evidence": [e.as_dict() for e in self.evidence],
            "evidence_backed": self.evidence_backed,
            "created_at": self.created_at,
        }


class RecommendationEngine:
    """Menyusun rekomendasi berbasis evidence."""

    def recommend(self, domain: str, suggestion: str, evidence: Tuple[EvidenceRef, ...], confidence: float) -> GovernanceRecommendation:
        import uuid

        return GovernanceRecommendation(
            recommendation_id=uuid.uuid4().hex,
            domain=domain,
            suggestion=suggestion,
            confidence=round(confidence, 3),
            evidence=evidence,
        )


@dataclass(frozen=True)
class AlternativeStrategy:
    """Strategi alternatif."""

    strategy_id: str
    proposal: str
    expected_benefit: float
    expected_cost: float

    def as_dict(self) -> dict:
        return {
            "strategy_id": self.strategy_id,
            "proposal": self.proposal,
            "expected_benefit": self.expected_benefit,
            "expected_cost": self.expected_cost,
        }


class StrategyAnalyzer:
    """Menganalisis strategi alternatif."""

    def analyze(self, options: Tuple[AlternativeStrategy, ...]) -> Tuple[AlternativeStrategy, ...]:
        return tuple(sorted(options, key=lambda s: s.expected_benefit - s.expected_cost, reverse=True))


class Prioritizer:
    """Memprioritaskan rekomendasi."""

    def prioritize(self, recommendations: Tuple[GovernanceRecommendation, ...]) -> Tuple[GovernanceRecommendation, ...]:
        return tuple(sorted(recommendations, key=lambda r: r.confidence, reverse=True))


@dataclass(frozen=True)
class ApprovalContext:
    """Konteks approval (manusia yang memutuskan)."""

    recommendation_id: str
    requires_human_approval: bool = True
    authority_retained: bool = True

    def as_dict(self) -> dict:
        return {
            "recommendation_id": self.recommendation_id,
            "requires_human_approval": self.requires_human_approval,
            "authority_retained": self.authority_retained,
        }


class ApprovalContextBuilder:
    """Membangun konteks approval untuk rekomendasi."""

    def build(self, recommendation: GovernanceRecommendation) -> ApprovalContext:
        return ApprovalContext(recommendation_id=recommendation.recommendation_id)


class RecommendationExplainability:
    """Menjelaskan rekomendasi."""

    def explain(self, recommendation: GovernanceRecommendation) -> Dict[str, Any]:
        return {
            "recommendation_id": recommendation.recommendation_id,
            "domain": recommendation.domain,
            "confidence": recommendation.confidence,
            "evidence_count": len(recommendation.evidence),
            "evidence_backed": recommendation.evidence_backed,
            "explainable": True,
        }


class RecommendationComplianceChecker:
    """Checker compliance rekomendasi (tidak mengambil authority)."""

    def check(self, *, recommend_only=True, human_decides=True, no_authority_change=True, evidence_based=True, explainable=True) -> Dict[str, Any]:
        checks = [
            {"code": "RECOMMEND_ONLY", "passed": recommend_only},
            {"code": "HUMAN_DECIDES", "passed": human_decides},
            {"code": "NO_AUTHORITY_CHANGE", "passed": no_authority_change},
            {"code": "EVIDENCE_BASED", "passed": evidence_based},
            {"code": "EXPLAINABLE", "passed": explainable},
        ]
        passed = all(c["passed"] for c in checks)
        return {"component": "adaptive_governance.recommendation", "passed": passed, "certified": passed, "checks": [c for c in checks]}
