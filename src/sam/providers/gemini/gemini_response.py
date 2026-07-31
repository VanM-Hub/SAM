"""Gemini Response — response spesifik Gemini (Sprint 232).

Membungkus response Gemini generateContent menjadi LLMResponse generik.
Immutable, preview-first, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from ..llm.llm_response import LLMResponse


@dataclass(frozen=True)
class GeminiResponse:
    """Response Gemini (immutable)."""
    response_id: str
    request_id: str
    model: str
    text: str = ""
    finish_reason: str = "STOP"
    usage: Dict[str, int] = field(default_factory=dict)
    provider_id: str = "gemini"
    external_calls: int = 0

    def to_llm(self) -> LLMResponse:
        usage = dict(self.usage)
        norm = {
            "prompt_tokens": usage.get(
                "prompt_tokens", usage.get("promptTokenCount", 0)
            ),
            "completion_tokens": usage.get(
                "completion_tokens", usage.get("candidatesTokenCount", 0)
            ),
        }
        norm["total_tokens"] = usage.get(
            "total_tokens", norm["prompt_tokens"] + norm["completion_tokens"]
        )
        return LLMResponse(
            response_id=self.response_id,
            request_id=self.request_id,
            provider_id=self.provider_id,
            model=self.model,
            ok=True,
            text=self.text,
            finish_reason=self.finish_reason,
            usage=norm,
            external_calls=self.external_calls,
        )
