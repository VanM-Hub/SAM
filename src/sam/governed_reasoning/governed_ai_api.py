"""Governed AI API - WP-27 (MISSION-4.4 / IP-4.4-003).

Antarmuka terpadu untuk seluruh capability AI reasoning operasional di
bawah Governance. Read-only; tidak menghasilkan authority.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Tuple

from .structured_reasoning import EvidenceRef
from .operational_ai import (
    ConversationReasoning,
    DiagnosisReasoning,
    DomainReasoning,
    InvestigationReasoning,
    LearningAssistedReasoning,
    OperationalExplainability,
    RecommendationReasoning,
)


@dataclass(frozen=True)
class GovernedAIResponse:
    """Response terpadu AI reasoning."""

    domain: str
    reasoning: DomainReasoning
    explanation: Dict[str, Any]

    def as_dict(self) -> dict:
        return {
            "domain": self.domain,
            "reasoning": self.reasoning.as_dict(),
            "explanation": self.explanation,
        }


class GovernedAIAPI:
    """Facade untuk AI reasoning operasional (di bawah governance)."""

    def __init__(
        self,
        *,
        investigation: InvestigationReasoning,
        diagnosis: DiagnosisReasoning,
        recommendation: RecommendationReasoning,
        learning: LearningAssistedReasoning,
        conversation: ConversationReasoning,
    ) -> None:
        self._investigation = investigation
        self._diagnosis = diagnosis
        self._recommendation = recommendation
        self._learning = learning
        self._conversation = conversation

    def investigate(
        self, question: str, evidences: Tuple[EvidenceRef, ...], **ctx: Any
    ) -> GovernedAIResponse:
        reasoning = self._investigation.reason(question, evidences, **ctx)
        return GovernedAIResponse(
            domain="investigation",
            reasoning=reasoning,
            explanation=OperationalExplainability.explain(reasoning),
        )

    def diagnose(
        self, question: str, evidences: Tuple[EvidenceRef, ...], **ctx: Any
    ) -> GovernedAIResponse:
        reasoning = self._diagnosis.reason(question, evidences, **ctx)
        return GovernedAIResponse(
            domain="diagnosis",
            reasoning=reasoning,
            explanation=OperationalExplainability.explain(reasoning),
        )

    def recommend(
        self, question: str, evidences: Tuple[EvidenceRef, ...], **ctx: Any
    ) -> GovernedAIResponse:
        reasoning = self._recommendation.reason(question, evidences, **ctx)
        return GovernedAIResponse(
            domain="recommendation",
            reasoning=reasoning,
            explanation=OperationalExplainability.explain(reasoning),
        )

    def learn(
        self, question: str, evidences: Tuple[EvidenceRef, ...], **ctx: Any
    ) -> GovernedAIResponse:
        reasoning = self._learning.reason(question, evidences, **ctx)
        return GovernedAIResponse(
            domain="learning",
            reasoning=reasoning,
            explanation=OperationalExplainability.explain(reasoning),
        )

    def converse(
        self, message: str, evidences: Tuple[EvidenceRef, ...], **ctx: Any
    ) -> GovernedAIResponse:
        reasoning = self._conversation.respond(message, evidences, **ctx)
        return GovernedAIResponse(
            domain="conversation",
            reasoning=reasoning,
            explanation=OperationalExplainability.explain(reasoning),
        )
