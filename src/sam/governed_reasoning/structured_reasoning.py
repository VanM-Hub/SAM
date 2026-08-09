"""Structured Reasoning Engine - WP-11/12/13 (MISSION-4.4 / IP-4.4-002).

Reasoning AI berbasis evidence dan terstruktur. Reasoning selalu menggunakan
evidence, Confidence tersedia, dapat diverifikasi, dan tidak menghasilkan
authority.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class EvidenceRef:
    """Referensi evidence untuk reasoning."""

    evidence_id: str
    source_type: str = ""
    source_id: str = ""

    def as_dict(self) -> dict:
        return {
            "evidence_id": self.evidence_id,
            "source_type": self.source_type,
            "source_id": self.source_id,
        }


@dataclass(frozen=True)
class ReasoningContext:
    """Konteks reasoning (resolved)."""

    question: str
    investigation_id: str = ""
    provider_id: str = ""
    scope: str = ""

    def as_dict(self) -> dict:
        return {
            "question": self.question,
            "investigation_id": self.investigation_id,
            "provider_id": self.provider_id,
            "scope": self.scope,
        }


@dataclass(frozen=True)
class ReasoningStep:
    """Satu langkah reasoning (structured)."""

    step_id: str
    kind: str  # premise | inference | conclusion
    content: str
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "kind": self.kind,
            "content": self.content,
            "evidence_refs": list(self.evidence_refs),
        }


@dataclass(frozen=True)
class StructuredReasoning:
    """Hasil reasoning terstruktur."""

    reasoning_id: str
    context: ReasoningContext
    steps: Tuple[ReasoningStep, ...] = field(default_factory=tuple)
    conclusion: str = ""
    created_at: str = field(default_factory=_now_utc)

    @property
    def is_evidence_backed(self) -> bool:
        return all(s.evidence_refs for s in self.steps)

    @property
    def total_evidence(self) -> int:
        return len({e for s in self.steps for e in s.evidence_refs})

    def as_dict(self) -> dict:
        return {
            "reasoning_id": self.reasoning_id,
            "context": self.context.as_dict(),
            "steps": [s.as_dict() for s in self.steps],
            "conclusion": self.conclusion,
            "created_at": self.created_at,
            "is_evidence_backed": self.is_evidence_backed,
        }


class ContextResolver:
    """Menyelesaikan konteks reasoning (menentukan scope & target)."""

    @staticmethod
    def resolve(question: str, **kwargs: Any) -> ReasoningContext:
        return ReasoningContext(
            question=question,
            investigation_id=kwargs.get("investigation_id", ""),
            provider_id=kwargs.get("provider_id", ""),
            scope=kwargs.get("scope", ""),
        )


class StructuredReasoningEngine:
    """Mesin reasoning terstruktur berbasis evidence."""

    def __init__(
        self,
        reasoning_fn: Callable[[ReasoningContext, Tuple[EvidenceRef, ...]], Tuple[ReasoningStep, str]],
    ) -> None:
        self._reasoning_fn = reasoning_fn

    def reason(
        self,
        question: str,
        evidences: Tuple[EvidenceRef, ...],
        **context_kwargs: Any,
    ) -> StructuredReasoning:
        context = ContextResolver.resolve(question, **context_kwargs)
        steps, conclusion = self._reasoning_fn(context, evidences)
        return StructuredReasoning(
            reasoning_id=uuid.uuid4().hex,
            context=context,
            steps=tuple(steps),
            conclusion=conclusion,
        )
