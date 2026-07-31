"""Conversation Chat — bridge conversation <-> model chat (Sprint 241).

Program B — Model Runtime Integration.
Read-only bridge; preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from .chat_session import ChatSession, ChatSessionStore
from ..model_runtime.model_message import ModelMessage
from ..model_runtime.model_request import ModelRequest


@dataclass(frozen=True)
class ConversationChatResult:
    """Hasil komposisi conversation <-> chat (immutable)."""
    conversation_id: str
    session: ChatSession
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "session": self.session.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ConversationChat:
    """Bridge conversation <-> chat. Read-only."""

    def __init__(self, store: ChatSessionStore | None = None) -> None:
        self._store = store or ChatSessionStore()

    def attach(self, conversation_id: str, chat: ChatModelSource) -> ConversationChatResult:
        session = self._store.create(conversation_id, chat.model())
        return ConversationChatResult(
            conversation_id=conversation_id,
            session=session,
            preview_only=True,
            external_calls=0,
        )

    def send(self, conversation_id: str, content: str) -> bool:
        return self._store.add_message(
            conversation_id,
            ModelMessage(role="user", content=content),
        )

    def store(self) -> ChatSessionStore:
        return self._store


class ChatModelSource:
    """Adapter ringan ke model chat. Read-only, preview-only."""

    def __init__(self, chat: "ChatModel") -> None:
        self._chat = chat

    def model(self) -> "ChatModel":
        return self._chat
