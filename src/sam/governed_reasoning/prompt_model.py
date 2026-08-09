"""Governed Prompt Model - WP-03 (MISSION-4.4 / IP-4.4-001).

Model Prompt yang berada di bawah Governance. Seluruh Prompt memiliki
identitas, context, dapat ditelusuri, dan immutable setelah dikirim.
"""
from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class PromptClassification:
    INVESTIGATION = "investigation"
    DIAGNOSIS = "diagnosis"
    RECOMMENDATION = "recommendation"
    ANALYSIS = "analysis"
    EXPLANATION = "explanation"

    _VALID = (
        INVESTIGATION,
        DIAGNOSIS,
        RECOMMENDATION,
        ANALYSIS,
        EXPLANATION,
    )

    @classmethod
    def valid(cls, classification: str) -> bool:
        return classification in cls._VALID


@dataclass(frozen=True)
class PromptContext:
    """Konteks prompt."""

    investigation_id: str = ""
    diagnosis_id: str = ""
    provider_id: str = ""
    purpose: str = ""

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "diagnosis_id": self.diagnosis_id,
            "provider_id": self.provider_id,
            "purpose": self.purpose,
        }


@dataclass(frozen=True)
class PromptPolicy:
    """Kebijakan prompt (constraint governance)."""

    max_tokens: int = 2048
    require_evidence: bool = True
    allow_system_role: bool = True

    def as_dict(self) -> dict:
        return {
            "max_tokens": self.max_tokens,
            "require_evidence": self.require_evidence,
            "allow_system_role": self.allow_system_role,
        }


@dataclass(frozen=True)
class PromptMetadata:
    """Metadata prompt."""

    created_at: str = field(default_factory=_now_utc)
    created_by: str = "governed_reasoning"
    classification: str = PromptClassification.ANALYSIS

    def as_dict(self) -> dict:
        return {
            "created_at": self.created_at,
            "created_by": self.created_by,
            "classification": self.classification,
        }


@dataclass(frozen=True)
class Prompt:
    """Prompt yang di-govern (immutable setelah dikirim)."""

    prompt_id: str
    content: str
    system: str = ""
    context: PromptContext = field(default_factory=PromptContext)
    policy: PromptPolicy = field(default_factory=PromptPolicy)
    metadata: PromptMetadata = field(default_factory=PromptMetadata)
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    submitted: bool = False

    @classmethod
    def create(
        cls,
        *,
        content: str,
        system: str = "",
        context: Optional[PromptContext] = None,
        policy: Optional[PromptPolicy] = None,
        classification: str = PromptClassification.ANALYSIS,
        evidence_refs: Tuple[str, ...] = (),
    ) -> "Prompt":
        if not PromptClassification.valid(classification):
            raise ValueError(f"Invalid classification: {classification!r}")
        return cls(
            prompt_id=uuid.uuid4().hex,
            content=content,
            system=system,
            context=context or PromptContext(),
            policy=policy or PromptPolicy(),
            metadata=PromptMetadata(classification=classification),
            evidence_refs=evidence_refs,
        )

    def as_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "content": self.content,
            "system": self.system,
            "context": self.context.as_dict(),
            "policy": self.policy.as_dict(),
            "metadata": self.metadata.as_dict(),
            "evidence_refs": list(self.evidence_refs),
            "submitted": self.submitted,
        }


class PromptRepository:
    """Penyimpanan prompt (immutable, append-only)."""

    def __init__(self) -> None:
        self._prompts: Dict[str, Prompt] = {}

    def add(self, prompt: Prompt) -> None:
        self._prompts[prompt.prompt_id] = prompt

    def get(self, prompt_id: str) -> Optional[Prompt]:
        return self._prompts.get(prompt_id)

    def all(self) -> Tuple[Prompt, ...]:
        return tuple(self._prompts.values())

    def count(self) -> int:
        return len(self._prompts)
