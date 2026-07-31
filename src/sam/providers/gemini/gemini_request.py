"""Gemini Request — request spesifik Gemini (Sprint 232).

Membungkus LLMRequest generik ke format Gemini generateContent.
Immutable, preview-first, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from ..llm.llm_request import LLMRequest
from ..llm.llm_message import LLMMessage


@dataclass(frozen=True)
class GeminiRequest:
    """Request Gemini generateContent (immutable)."""
    request_id: str
    model: str
    messages: Tuple[LLMMessage, ...] = field(default_factory=tuple)
    temperature: float = 0.2
    max_output_tokens: int = 1024
    system: Optional[str] = None
    provider_id: str = "gemini"
    mode: str = "preview"
    external_calls: int = 0

    @classmethod
    def from_llm(cls, request: LLMRequest) -> "GeminiRequest":
        return cls(
            request_id=request.request_id,
            model=request.model,
            messages=request.messages,
            temperature=request.temperature,
            max_output_tokens=request.max_tokens,
            system=request.system,
            provider_id=request.provider_id,
            mode=request.mode,
            external_calls=request.external_calls,
        )

    def wire_parts(self) -> list:
        """Format konten ke list parts Gemini (deterministik, tanpa network)."""
        parts = []
        if self.system:
            parts.append({"text": self.system})
        for m in self.messages:
            parts.append({"text": m.content})
        return parts

    def as_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "model": self.model,
            "contents": self.wire_parts(),
            "generationConfig": {
                "temperature": self.temperature,
                "maxOutputTokens": self.max_output_tokens,
            },
            "provider_id": self.provider_id,
            "mode": self.mode,
            "external_calls": self.external_calls,
        }
