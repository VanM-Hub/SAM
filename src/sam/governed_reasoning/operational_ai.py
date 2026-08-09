"""Operational AI - WP-21..26 (MISSION-4.4 / IP-4.4-003).

Menghubungkan AI Reasoning dengan capability operasional SAM: investigasi,
diagnosis, rekomendasi, pembelajaran, percakapan. Seluruh reasoning
berbasis evidence & dijelaskan (Operational Explainability). Read-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple

from .structured_reasoning import (
    EvidenceRef,
    ReasoningStep,
    StructuredReasoningEngine,
)


@dataclass(frozen=True)
class DomainReasoning:
    """Hasil reasoning untuk satu domain operasional."""

    domain: str  # investigation | diagnosis | recommendation | learning | conversation
    reasoning_id: str
    contextual_input: str
    conclusion: str = ""
    steps: Tuple[ReasoningStep, ...] = field(default_factory=tuple)
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "domain": self.domain,
            "reasoning_id": self.reasoning_id,
            "contextual_input": self.contextual_input,
            "conclusion": self.conclusion,
            "steps": [s.as_dict() for s in self.steps],
            "evidence_refs": list(self.evidence_refs),
        }


class _DomainEngine:
    """Adaptor reasoning engine untuk sebuah domain."""

    def __init__(
        self, domain: str, engine: StructuredReasoningEngine
    ) -> None:
        self._domain = domain
        self._engine = engine

    def reason(
        self,
        contextual_input: str,
        evidences: Tuple[EvidenceRef, ...],
        **ctx: Any,
    ) -> DomainReasoning:
        reasoning = self._engine.reason(
            contextual_input, evidences, scope=self._domain, **ctx
        )
        return DomainReasoning(
            domain=self._domain,
            reasoning_id=reasoning.reasoning_id,
            contextual_input=contextual_input,
            conclusion=reasoning.conclusion,
            steps=reasoning.steps,
            evidence_refs=tuple(
                e for s in reasoning.steps for e in s.evidence_refs
            ),
        )


class InvestigationReasoning(_DomainEngine):
    def __init__(self, engine: StructuredReasoningEngine) -> None:
        super().__init__("investigation", engine)


class DiagnosisReasoning(_DomainEngine):
    def __init__(self, engine: StructuredReasoningEngine) -> None:
        super().__init__("diagnosis", engine)


class RecommendationReasoning(_DomainEngine):
    def __init__(self, engine: StructuredReasoningEngine) -> None:
        super().__init__("recommendation", engine)


class LearningAssistedReasoning(_DomainEngine):
    def __init__(self, engine: StructuredReasoningEngine) -> None:
        super().__init__("learning", engine)


class ConversationReasoning(_DomainEngine):
    """Reasoning untuk percakapan (conversation)."""

    def __init__(self, engine: StructuredReasoningEngine) -> None:
        super().__init__("conversation", engine)

    def respond(
        self, user_message: str, evidences: Tuple[EvidenceRef, ...], **ctx: Any
    ) -> DomainReasoning:
        return self.reason(user_message, evidences, **ctx)


class OperationalExplainability:
    """Menjelaskan reasoning operasional (read-only)."""

    @staticmethod
    def explain(domain_reasoning: DomainReasoning) -> Dict[str, Any]:
        return {
            "domain": domain_reasoning.domain,
            "reasoning_id": domain_reasoning.reasoning_id,
            "input": domain_reasoning.contextual_input,
            "conclusion": domain_reasoning.conclusion,
            "step_chain": [
                (s.kind, s.content) for s in domain_reasoning.steps
            ],
            "evidence_chain": list(
                dict.fromkeys(domain_reasoning.evidence_refs)
            ),
        }
