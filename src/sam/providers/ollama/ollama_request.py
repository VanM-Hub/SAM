"""Ollama Request — request spesifik Ollama (Sprint 234).

Membungkus LLMRequest generik ke format Ollama /api/generate.
Immutable, preview-first, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from ..llm.llm_request import LLMRequest
from ..llm.llm_message import LLMMessage


@dataclass(frozen=True)
class OllamaRequest:
    """Request Ollama /api/generate (immutable)."""
    request_id: str
    model: str
    messages: Tuple[LLMMessage, ...] = field(default_factory=tuple)
    temperature: float = 0.2
    num_predict: int = 1024
    system: Optional[str] = None
    provider_id: str = "ollama"
    mode: str = "preview"
    external_calls: int = 0

    @classmethod
    def from_llm(cls, request: LLMRequest) -> "OllamaRequest":
        return cls(
            request_id=request.request_id,
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            num_predict=request.max_tokens,
            system=request.system,
            provider_id=request.provider_id,
            mode=request.mode,
            external_calls=request.external_calls,
        )

    def prompt_text(self) -> str:
        parts = []
        if self.system:
            parts.append(f"System: {self.system}")
        for m in self.messages:
            parts.append(m.content)
        return "\n".join(parts)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "prompt": self.prompt_text(),
            "options": {"temperature": self.temperature, "num_predict": self.num_predict},
            "provider_id": self.provider_id,
            "mode": self.mode,
            "external_calls": self.external_calls,
        }
