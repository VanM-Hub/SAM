"""recommendation — WP-12 (IP-3.1-001).

RecommendationService turns a validated explanation into a Recommendation.

Per directive:

  *  Output : Recommendation { Evidence, Confidence, Tradeoff, Missing
             Information }.
  *  "Tidak boleh menghasilkan recommendation tanpa evidence."  — Multiple
     implementations of this directive: a recommendation MUST carry at least
     one evidence item. If none, the service must NOT emit a recommendation
     (it raises or returns a no-op). Here we return an empty Recommendation
     flagged ``has_evidence=False`` so the caller (gateway/report) can refuse.

Deterministic, no AI: recommendation content is derived only from the
explanation's evidence + confidence.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List

from sam.governance_intelligence.explanation.decision import DecisionExplanation
from sam.governance_intelligence.knowledge.models import KnowledgeItem
from sam.governance_intelligence.knowledge.repository import EvidenceRepository


@dataclass(frozen=True)
class Recommendation:
    statement: str
    evidence: List[KnowledgeItem] = field(default_factory=list)
    confidence: float = 0.0
    tradeoff: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)
    has_evidence: bool = False

    def public_dict(self) -> dict:
        return {
            "statement": self.statement,
            "evidence": [e.public_dict() for e in self.evidence],
            "confidence": self.confidence,
            "tradeoff": list(self.tradeoff),
            "missing_information": list(self.missing_information),
            "has_evidence": self.has_evidence,
        }


class RecommendationService:
    """WP-12 implementation."""

    def __init__(self, evidence_repo: EvidenceRepository) -> None:
        self._evidence = evidence_repo

    def build(self, goal: str, explanation: DecisionExplanation) -> Recommendation:
        evidence = list(explanation.evidence)
        if not evidence:
            # Directive: no recommendation without evidence.
            return Recommendation(
                statement=f"No recommendation for '{goal}' — no evidence available.",
                evidence=[],
                confidence=0.0,
                missing_information=list(explanation.missing_evidence),
                has_evidence=False,
            )
        statement = (
            f"Proceed with '{goal}': {len(evidence)} evidence item(s) support "
            f"it; confidence {explanation.confidence:.1f}."
        )
        return Recommendation(
            statement=statement,
            evidence=evidence,
            confidence=explanation.confidence,
            tradeoff=[f"Requires {e.key}" for e in evidence],
            missing_information=list(explanation.missing_evidence),
            has_evidence=True,
        )
