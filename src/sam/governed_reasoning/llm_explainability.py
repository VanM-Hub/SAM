"""LLM Explainability - WP-08 (MISSION-4.4 / IP-4.4-001).

Menjelaskan seluruh proses interaksi dengan LLM. Prompt dapat ditelusuri,
Response memiliki evidence, Provider Trace tersedia, seluruh proses dapat
diaudit.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from .prompt_model import Prompt
from .prompt_execution import PromptResponse, ExecutionSession
from .llm_provider import LLMProviderAdapter


@dataclass(frozen=True)
class ProviderTrace:
    """Trace provider untuk sebuah eksekusi."""

    provider_id: str
    vendor: str = ""
    model: str = ""
    session_id: str = ""

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "vendor": self.vendor,
            "model": self.model,
            "session_id": self.session_id,
        }


@dataclass(frozen=True)
class ExecutionTimeline:
    """Timeline eksekusi."""

    session_id: str
    steps: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "steps": [list(s) for s in self.steps],
        }


@dataclass(frozen=True)
class LLMExplanation:
    """Penjelasan interaksi LLM."""

    prompt_id: str
    session_id: str
    prompt_trace: Dict[str, Any]
    provider_trace: ProviderTrace
    timeline: ExecutionTimeline
    evidence_chain: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "prompt_id": self.prompt_id,
            "session_id": self.session_id,
            "prompt_trace": self.prompt_trace,
            "provider_trace": self.provider_trace.as_dict(),
            "timeline": self.timeline.as_dict(),
            "evidence_chain": list(self.evidence_chain),
        }


class LLMExplainer:
    """Menjelaskan interaksi LLM (read-only)."""

    def explain(
        self,
        prompt: Prompt,
        session: ExecutionSession,
        response: Optional[PromptResponse],
        provider: Optional[LLMProviderAdapter],
    ) -> LLMExplanation:
        provider_trace = ProviderTrace(
            provider_id=session.provider_id,
            vendor=provider.metadata.vendor if provider else "",
            model=provider.metadata.model if provider else "",
            session_id=session.session_id,
        )
        timeline = ExecutionTimeline(
            session_id=session.session_id,
            steps=(
                ("created", "session created"),
                ("validated", "prompt validated"),
                ("executed", "provider invoked"),
                ("completed", "response captured"),
            ),
        )
        return LLMExplanation(
            prompt_id=prompt.prompt_id,
            session_id=session.session_id,
            prompt_trace={
                "classification": prompt.metadata.classification,
                "provider_id": prompt.context.provider_id,
                "evidence_refs": list(prompt.evidence_refs),
            },
            provider_trace=provider_trace,
            timeline=timeline,
            evidence_chain=prompt.evidence_refs,
        )


class LLMExplainabilityAPI:
    """Public read-only API explainability LLM."""

    def __init__(self, explainer: LLMExplainer) -> None:
        self._explainer = explainer

    def explain(
        self,
        prompt: Prompt,
        session: ExecutionSession,
        response: Optional[PromptResponse],
        provider: Optional[LLMProviderAdapter],
    ) -> Dict[str, Any]:
        return self._explainer.explain(prompt, session, response, provider).as_dict()
