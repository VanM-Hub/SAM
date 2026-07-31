"""Anthropic Response — response spesifik Anthropic (Sprint 231).

Membungkus response Anthropic Messages menjadi LLMResponse generik.
Immutable, preview-first, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from ..llm.llm_response import LLMResponse


@dataclass(frozen=True)
class AnthropicResponse:
    """Response Anthropic (immutable)."""
    response_id: str
    request_id: str
    model: str
    text: str = ""
    stop_reason: str = "end_turn"
    usage: Dict[str, int] = field(default_factory=dict)
    provider_id: str = "anthropic"
    external_calls: int = 0

    def to_llm(self) -> LLMResponse:
        usage = dict(self.usage)
        # Normalisasi kunci Anthropic -> OpenAI-style generik.
        norm = {
            "prompt_tokens": usage.get("prompt_tokens", usage.get("input_tokens", 0)),
            "completion_tokens": usage.get("completion_tokens", usage.get("output_tokens", 0)),
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
            finish_reason=self.stop_reason,
            usage=norm,
            external_calls=self.external_calls,
        )
