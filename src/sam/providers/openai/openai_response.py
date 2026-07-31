"""OpenAI Response — response spesifik OpenAI (Sprint 230).

Membungkus response OpenAI (chat completion) menjadi LLMResponse generik.
Immutable, preview-first, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from ..llm.llm_response import LLMResponse


@dataclass(frozen=True)
class OpenAIResponse:
    """Response OpenAI (immutable)."""
    response_id: str
    request_id: str
    model: str
    text: str = ""
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)
    provider_id: str = "openai"
    external_calls: int = 0

    def to_llm(self) -> LLMResponse:
        return LLMResponse(
            response_id=self.response_id,
            request_id=self.request_id,
            provider_id=self.provider_id,
            model=self.model,
            ok=True,
            text=self.text,
            finish_reason=self.finish_reason,
            usage=dict(self.usage),
            external_calls=self.external_calls,
        )
