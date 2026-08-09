"""Reasoning Explainability - WP-38 (MISSION-5.1 / IP-5.1-004).

Explainability untuk reasoning result: evidence lineage + alasan operasional
yang dapat diaudit. Tidak mengungkap internal chain-of-thought model.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .reasoning_request import ReasoningRequest
from .reasoning_response import ReasoningResponse


@dataclass(frozen=True)
class ReasoningExplanation:
    """Penjelasan reasoning yang dapat diaudit."""

    request_id: str
    objective: str
    context_sources: Tuple[str, ...] = field(default_factory=tuple)
    evidence_lineage: Tuple[str, ...] = field(default_factory=tuple)
    provider_model: str = ""
    conclusion: str = ""
    confidence: float = 0.0
    recommendation: str = ""
    limitations: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "request_id": self.request_id,
            "objective": self.objective,
            "context_sources": list(self.context_sources),
            "evidence_lineage": list(self.evidence_lineage),
            "provider_model": self.provider_model,
            "conclusion": self.conclusion,
            "confidence": self.confidence,
            "recommendation": self.recommendation,
            "limitations": list(self.limitations),
        }


class ReasoningExplainer:
    """Membangun explanation berbasis request & response."""

    def explain(
        self, request: ReasoningRequest, response: ReasoningResponse
    ) -> ReasoningExplanation:
        sources = []
        if request.resolved_context is not None:
            sources = list(request.resolved_context.base.provenance)
        return ReasoningExplanation(
            request_id=request.request_id,
            objective=request.objective,
            context_sources=tuple(sources),
            evidence_lineage=tuple(response.evidence_refs),
            provider_model=f"{response.provider_id}:{response.model_id}",
            conclusion=response.conclusion,
            confidence=response.confidence,
            recommendation=response.recommendation,
            limitations=response.limitations,
        )
