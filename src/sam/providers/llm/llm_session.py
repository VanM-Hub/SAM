"""LLM Session — sesi generik percakapan LLM (Sprint 229)."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Tuple

from .llm_message import LLMMessage


class LLMSessionState(str, Enum):
    """Status sesi LLM."""
    CREATED = "created"
    OPEN = "open"
    GENERATING = "generating"
    COMPLETED = "completed"
    ERROR = "error"
    CLOSED = "closed"


@dataclass(frozen=True)
class LLMSession:
    """Sesi LLM immutable. Transisi menghasilkan instance baru."""
    session_id: str
    provider_id: str
    model: str
    state: LLMSessionState = LLMSessionState.CREATED
    messages: Tuple[LLMMessage, ...] = field(default_factory=tuple)
    metadata: Dict[str, str] = field(default_factory=dict)
    external_calls: int = 0

    def open(self) -> "LLMSession":
        return LLMSession(
            self.session_id, self.provider_id, self.model,
            LLMSessionState.OPEN, self.messages, self.metadata, self.external_calls,
        )

    def append(self, message: LLMMessage) -> "LLMSession":
        return LLMSession(
            self.session_id, self.provider_id, self.model,
            self.state, self.messages + (message,),
            self.metadata, self.external_calls,
        )

    def complete(self) -> "LLMSession":
        return LLMSession(
            self.session_id, self.provider_id, self.model,
            LLMSessionState.COMPLETED, self.messages,
            self.metadata, self.external_calls,
        )

    @property
    def message_count(self) -> int:
        return len(self.messages)
