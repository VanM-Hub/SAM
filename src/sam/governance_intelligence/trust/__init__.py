"""WP-20 - Trust Score Engine (IP-3.1-002).

Trust is NOT a confidence model. Trust is computed from the QUALITY of
evidence. Dimensions (example):

    evidence completeness
    source authority
    consistency
    freshness
    verification status
    constitutional compliance

Output:

    TrustAssessment
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import EvidenceRepository


@dataclass(frozen=True)
class TrustAssessment:
    """Immutable trust assessment over an evidence set (WP-20 output)."""

    overall: float
    completeness: float
    source_authority: float
    consistency: float
    freshness: float
    verification_status: float
    constitutional_compliance: float

    def public_dict(self) -> dict:
        return {
            "overall": self.overall,
            "completeness": self.completeness,
            "source_authority": self.source_authority,
            "consistency": self.consistency,
            "freshness": self.freshness,
            "verification_status": self.verification_status,
            "constitutional_compliance": self.constitutional_compliance,
        }


class TrustScoreEngine:
    """WP-20 implementation. Deterministic trust scoring from evidence quality."""

    def __init__(self, evidence: EvidenceRepository) -> None:
        self._evidence = evidence

    def assess(self, items: List[KnowledgeItem]) -> TrustAssessment:
        n = len(items)
        if n == 0:
            return TrustAssessment(
                overall=0.0,
                completeness=0.0,
                source_authority=0.0,
                consistency=0.0,
                freshness=0.0,
                verification_status=0.0,
                constitutional_compliance=1.0,  # no evidence -> no violation
            )
        completeness = self._completeness(items, n)
        authority = self._authority(items, n)
        consistency = self._consistency(items, n)
        freshness = self._freshness(items, n)
        verification = self._verification(items, n)
        compliance = self._compliance(items, n)
        overall = round(
            (completeness + authority + consistency + freshness + verification + compliance) / 6.0,
            2,
        )
        return TrustAssessment(
            overall=overall,
            completeness=completeness,
            source_authority=authority,
            consistency=consistency,
            freshness=freshness,
            verification_status=verification,
            constitutional_compliance=compliance,
        )

    # --- dimension scorers (0..1) -----------------------------------------
    def _completeness(self, items: List[KnowledgeItem], n: int) -> float:
        # items carrying content + signature are considered complete
        complete = sum(1 for it in items if it.content and it.signature)
        return round(complete / n, 2)

    def _authority(self, items: List[KnowledgeItem], n: int) -> float:
        # authoritative sources are normative/knowledge docs (mission, adr, policy, constitution)
        authoritative_terms = ("foundation", "mission", "adr", "policy", "constitution", "governance", "architecture")
        strong = 0
        for it in items:
            src = (it.source or "").lower()
            if any(t in src for t in authoritative_terms):
                strong += 1
        return round(strong / n, 2)

    def _consistency(self, items: List[KnowledgeItem], n: int) -> float:
        # items that agree (share the same governance basis token) count as consistent
        bases = [it.section or it.key for it in items]
        unique = len(set(bases))
        consistent = 1 - (unique - 1) / max(n - 1, 1)
        return round(max(consistent, 0.0), 2)

    def _freshness(self, items: List[KnowledgeItem], n: int) -> float:
        # freshness: items carrying a status/metadata freshness flag count as fresh
        fresh = 0
        for it in items:
            meta = it.metadata
            if meta.get("status") in ("Active", "Accepted", "Enforced", "Verified") or meta.get("fresh", False):
                fresh += 1
        return round(fresh / n, 2)

    def _verification(self, items: List[KnowledgeItem], n: int) -> float:
        verified = 0
        for it in items:
            if it.metadata.get("verified", False) or it.metadata.get("verification_status") in ("verified", "verified_stable"):
                verified += 1
        return round(verified / n, 2)

    def _compliance(self, items: List[KnowledgeItem], n: int) -> float:
        # items that are non-constitutional or mark a violation reduce compliance
        violations = 0
        for it in items:
            meta = it.metadata
            if meta.get("constitutional") is False or meta.get("violation") is True:
                violations += 1
        return round(1.0 - (violations / n), 2)
