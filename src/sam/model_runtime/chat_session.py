"""Chat Session — sesi chat (Sprint 241).

Program B — Model Runtime Integration.
Preview-only, deterministik, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from .chat_model import ChatModel
from .chat_history import ChatHistory
from ..model_runtime.model_message import ModelMessage
from ..model_runtime.model_context import ModelContext


@dataclass(frozen=True)
class ChatSession:
    """Sesi chat (immutable terhadap data statis; history dipegang terpisah)."""
    session_id: str
    chat: ChatModel
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "chat": self.chat.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ChatSessionStore:
    """Penyimpan sesi chat in-memory. No write eksternal."""

    def __init__(self) -> None:
        self._sessions: dict = {}

    def create(self, session_id: str, chat: ChatModel) -> ChatSession:
        session = ChatSession(session_id=session_id, chat=chat)
        self._sessions[session_id] = (session, ChatHistory(history_id=session_id))
        return session

    def get(self, session_id: str) -> Optional[ChatSession]:
        pair = self._sessions.get(session_id)
        return pair[0] if pair else None

    def history(self, session_id: str) -> ChatHistory:
        pair = self._sessions.get(session_id)
        if pair is None:
            raise KeyError(f"no session: {session_id}")
        return pair[1]

    def add_message(self, session_id: str, message: ModelMessage) -> bool:
        if session_id not in self._sessions:
            return False
        self._sessions[session_id][1].append(message)
        return True

    def count(self) -> int:
        return len(self._sessions)
