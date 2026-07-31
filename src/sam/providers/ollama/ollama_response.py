"""Ollama Response — response spesifik Ollama (Sprint 234).

Membungkus response Ollama /api/generate menjadi LLMResponse generik.
Immutable, preview-first, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from ..llm.llm_response import LLMResponse


@dataclass(frozen=True)
class OllamaResponse:
    """Response Ollama (immutable)."""
    response_id: str
    request_id: str
    model: str
    text: str = ""
    done: bool = True
    eval_count: int = 0
    prompt_eval_count: int = 0
    provider_id: str = "ollama"
    external_calls: int = 0

    def to_llm(self) -> LLMResponse:
        usage = {
            "prompt_tokens": self.prompt_eval_count,
            "completion_tokens": self.eval_count,
            "total_tokens": self.prompt_eval_count + self.eval_count,
        }
        return LLMResponse(
            response_id=self.response_id,
            request_id=self.request_id,
            provider_id=self.provider_id,
            model=self.model,
            ok=True,
            text=self.text,
            finish_reason="stop" if self.done else "in_progress",
            usage=usage,
            external_calls=self.external_calls,
        )
