"""LLM Message — representasi generik pesan LLM (Sprint 229)."""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class LLMRole(str, Enum):
    """Peran pesan dalam percakapan LLM."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"
    TOOL = "tool"
    FUNCTION = "function"


@dataclass(frozen=True)
class LLMMessage:
    """Sebuah pesan generik. Immutable."""
    role: LLMRole
    content: str
    name: Optional[str] = None
    tool_call_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> Dict[str, Any]:
        d: Dict[str, Any] = {
            "role": self.role.value,
            "content": self.content,
        }
        if self.name is not None:
            d["name"] = self.name
        if self.tool_call_id is not None:
            d["tool_call_id"] = self.tool_call_id
        return d


@dataclass(frozen=True)
class LLMMessageBuilder:
    """Builder deterministik untuk LLMMessage."""
    content: str
    role: LLMRole = LLMRole.USER

    def as_system(self) -> "LLMMessageBuilder":
        return LLMMessageBuilder(self.content, LLMRole.SYSTEM)

    def as_user(self) -> "LLMMessageBuilder":
        return LLMMessageBuilder(self.content, LLMRole.USER)

    def as_assistant(self) -> "LLMMessageBuilder":
        return LLMMessageBuilder(self.content, LLMRole.ASSISTANT)

    def build(self) -> LLMMessage:
        return LLMMessage(role=self.role, content=self.content)
