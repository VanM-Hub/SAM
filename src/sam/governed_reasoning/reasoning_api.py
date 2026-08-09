"""Reasoning API - WP-17 (MISSION-4.4 / IP-4.4-002).

Antarmuka standar untuk capability reasoning. Consisten, dapat
diintegrasikan, read-only query.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from .structured_reasoning import EvidenceRef, StructuredReasoning, StructuredReasoningEngine
from .confidence_assessment import ConfidenceAssessor
from .reasoning_verification import ReasoningVerifier
from .reasoning_explainability import ReasoningExplainer


@dataclass(frozen=True)
class ReasoningResult:
    """Hasil lengkap reasoning (read-only)."""

    reasoning: StructuredReasoning
    confidence: Dict[str, Any]
    verification: Dict[str, Any]
    explanation: Dict[str, Any]

    def as_dict(self) -> dict:
        return {
            "reasoning": self.reasoning.as_dict(),
            "confidence": self.confidence,
            "verification": self.verification,
            "explanation": self.explanation,
        }


class ReasoningAPI:
    """Facade reasoning (read-only, tanpa authority)."""

    def __init__(
        self,
        engine: StructuredReasoningEngine,
        *,
        assessor: Optional[ConfidenceAssessor] = None,
        verifier: Optional[ReasoningVerifier] = None,
        explainer: Optional[ReasoningExplainer] = None,
    ) -> None:
        self._engine = engine
        self._assessor = assessor or ConfidenceAssessor()
        self._verifier = verifier or ReasoningVerifier()
        self._explainer = explainer or ReasoningExplainer()

    def reason(
        self,
        question: str,
        evidences: Tuple[EvidenceRef, ...],
        **context_kwargs: Any,
    ) -> ReasoningResult:
        reasoning = self._engine.reason(question, evidences, **context_kwargs)
        confidence = self._assessor.assess(reasoning).as_dict()
        verification = self._verifier.verify(reasoning).as_dict()
        explanation = self._explainer.explain(reasoning).as_dict()
        return ReasoningResult(
            reasoning=reasoning,
            confidence=confidence,
            verification=verification,
            explanation=explanation,
        )

    def explain(self, reasoning: StructuredReasoning) -> Dict[str, Any]:
        return self._explainer.explain(reasoning).as_dict()
