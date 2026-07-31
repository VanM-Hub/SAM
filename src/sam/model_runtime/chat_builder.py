"""Chat Builder — builder deterministik untuk chat (Sprint 241).

Program B — Model Runtime Integration.
Deterministik, preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .chat_model import ChatModel
from ..model_runtime.model_message import ModelMessage
from ..model_runtime.model_context import ModelContext


@dataclass(frozen=True)
class ChatBuilder:
    """Builder deterministik untuk model chat dan konteks."""

    def build_model(
        self,
        chat_id: str,
        name: str,
        supports_system: bool = True,
        supports_tool: bool = True,
        max_context_tokens: Optional[int] = None,
    ) -> ChatModel:
        return ChatModel(
            chat_id=chat_id,
            name=name,
            supports_system=supports_system,
            supports_tool=supports_tool,
            max_context_tokens=max_context_tokens,
            preview_only=True,
            external_calls=0,
        )

    def system(self, content: str) -> ModelMessage:
        return ModelMessage(role="system", content=content)

    def user(self, content: str) -> ModelMessage:
        return ModelMessage(role="user", content=content)

    def assistant(self, content: str) -> ModelMessage:
        return ModelMessage(role="assistant", content=content)

    def tool(self, content: str, tool_call_id: str) -> ModelMessage:
        return ModelMessage(role="tool", content=content, tool_call_id=tool_call_id)

    def context(
        self,
        system: str = "",
        messages: List[ModelMessage] | None = None,
    ) -> ModelContext:
        return ModelContext(system=system, messages=list(messages or []))
