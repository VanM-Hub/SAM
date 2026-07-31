"""OpenAI Request — request spesifik OpenAI (Sprint 230).

Membungkus request generik ke format OpenAI (chat completion).
Immutable, preview-first, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from ..llm.llm_request import LLMRequest
from ..llm.llm_message import LLMMessage


@dataclass(frozen=True)
class OpenAIRequest:
    """Request OpenAI chat completion (immutable)."""
    request_id: str
    model: str
    messages: Tuple[LLMMessage, ...] = field(default_factory=tuple)
    temperature: float = 0.2
    max_tokens: int = 1024
    system: Optional[str] = None
    provider_id: str = "openai"
    mode: str = "preview"
    external_calls: int = 0

    @classmethod
    def from_llm(cls, request: LLMRequest) -> "OpenAIRequest":
        """Konversi dari LLMRequest generik. Deterministik, preview-first."""
        return cls(
            request_id=request.request_id,
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            system=request.system,
            provider_id=request.provider_id,
            mode=request.mode,
            external_calls=request.external_calls,
        )

    def wire_messages(self) -> list:
        """Format pesan sesuai wire-format OpenAI (tanpa network)."""
        out = []
        if self.system:
            out.append({"role": "system", "content": self.system})
        for m in self.messages:
            out.append({"role": m.role.value, "content": m.content})
        return out

    def as_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "messages": self.wire_messages(),
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "provider_id": self.provider_id,
            "mode": self.mode,
            "external_calls": self.external_calls,
        }
