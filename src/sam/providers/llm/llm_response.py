"""LLM Response — response generik dari penyedia LLM (Sprint 229)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple


@dataclass(frozen=True)
class LLMResponse:
    """Response generik dari LLM. Immutable, preview-first."""
    response_id: str
    request_id: str
    provider_id: str
    model: str
    ok: bool = True
    text: str = ""
    finish_reason: str = "stop"
    usage: Dict[str, int] = field(default_factory=dict)
    tool_calls: Tuple[str, ...] = field(default_factory=tuple)
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    latency_ms: float = 0.0
    external_calls: int = 0

    @property
    def prompt_tokens(self) -> int:
        return self.usage.get("prompt_tokens", 0)

    @property
    def completion_tokens(self) -> int:
        return self.usage.get("completion_tokens", 0)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "response_id": self.response_id,
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "model": self.model,
            "ok": self.ok,
            "text": self.text,
            "finish_reason": self.finish_reason,
            "usage": dict(self.usage),
            "tool_calls": list(self.tool_calls),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "latency_ms": self.latency_ms,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class LLMResponseBuilder:
    """Builder deterministik untuk LLMResponse."""
    response_id: str
    request_id: str
    provider_id: str
    model: str
    _text: str = ""
    _usage: Dict[str, int] = field(default_factory=dict)
    _finish: str = "stop"
    _tool_calls: Tuple[str, ...] = field(default_factory=tuple)

    def with_text(self, text: str) -> "LLMResponseBuilder":
        return LLMResponseBuilder(
            self.response_id, self.request_id, self.provider_id, self.model,
            text, self._usage, self._finish, self._tool_calls,
        )

    def with_usage(self, prompt: int, completion: int) -> "LLMResponseBuilder":
        usage = {
            "prompt_tokens": prompt,
            "completion_tokens": completion,
            "total_tokens": prompt + completion,
        }
        return LLMResponseBuilder(
            self.response_id, self.request_id, self.provider_id, self.model,
            self._text, usage, self._finish, self._tool_calls,
        )

    def build(self) -> LLMResponse:
        return LLMResponse(
            response_id=self.response_id,
            request_id=self.request_id,
            provider_id=self.provider_id,
            model=self.model,
            ok=True,
            text=self._text,
            finish_reason=self._finish,
            usage=dict(self._usage),
            tool_calls=self._tool_calls,
            external_calls=0,
        )
