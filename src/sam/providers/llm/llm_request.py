"""LLM Request — request generik ke penyedia LLM (Sprint 229)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from .llm_message import LLMMessage


@dataclass(frozen=True)
class LLMRequest:
    """Request generik ke LLM. Immutable, preview-first, external_calls=0."""
    request_id: str
    provider_id: str
    model: str
    messages: Tuple[LLMMessage, ...] = field(default_factory=tuple)
    temperature: float = 0.2
    max_tokens: int = 1024
    system: Optional[str] = None
    stop: Tuple[str, ...] = field(default_factory=tuple)
    tools: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Dict[str, Any] = field(default_factory=dict)
    mode: str = "preview"
    external_calls: int = 0

    def prompt_text(self) -> str:
        """Gabungkan pesan menjadi teks (deterministik, preview)."""
        parts = []
        if self.system:
            parts.append(f"[system] {self.system}")
        for m in self.messages:
            parts.append(f"[{m.role.value}] {m.content}")
        return "\n".join(parts)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "request_id": self.request_id,
            "provider_id": self.provider_id,
            "model": self.model,
            "messages": [m.as_dict() for m in self.messages],
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "system": self.system,
            "stop": list(self.stop),
            "tools": list(self.tools),
            "metadata": dict(self.metadata),
            "mode": self.mode,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class LLMRequestBuilder:
    """Builder deterministik untuk LLMRequest (immutable chain)."""
    request_id: str
    provider_id: str
    model: str
    _messages: Tuple[LLMMessage, ...] = field(default_factory=tuple)
    _temperature: float = 0.2
    _max_tokens: int = 1024
    _system: Optional[str] = None

    def with_system(self, system: str) -> "LLMRequestBuilder":
        return LLMRequestBuilder(
            self.request_id, self.provider_id, self.model,
            self._messages, self._temperature, self._max_tokens, system,
        )

    def add_message(self, message: LLMMessage) -> "LLMRequestBuilder":
        return LLMRequestBuilder(
            self.request_id, self.provider_id, self.model,
            self._messages + (message,),
            self._temperature, self._max_tokens, self._system,
        )

    def with_temperature(self, value: float) -> "LLMRequestBuilder":
        return LLMRequestBuilder(
            self.request_id, self.provider_id, self.model,
            self._messages, value, self._max_tokens, self._system,
        )

    def with_max_tokens(self, value: int) -> "LLMRequestBuilder":
        return LLMRequestBuilder(
            self.request_id, self.provider_id, self.model,
            self._messages, self._temperature, value, self._system,
        )

    def build(self) -> LLMRequest:
        return LLMRequest(
            request_id=self.request_id,
            provider_id=self.provider_id,
            model=self.model,
            messages=self._messages,
            temperature=self._temperature,
            max_tokens=self._max_tokens,
            system=self._system,
            mode="preview",
            external_calls=0,
        )
