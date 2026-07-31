"""Chat History — riwayat percakapan chat (Sprint 241).

Program B — Model Runtime Integration.
In-memory, preview-only, no write eksternal.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..model_runtime.model_message import ModelMessage


@dataclass(frozen=True)
class ChatHistoryEntry:
    """Satu entri riwayat chat (immutable)."""
    order: int
    message: ModelMessage

    def as_dict(self) -> dict:
        return {"order": self.order, "message": self.message.as_dict()}


class ChatHistory:
    """Riwayat chat in-memory. Read-only, deterministik."""

    def __init__(self, history_id: str = "chat-history") -> None:
        self._id = history_id
        self._entries: List[ChatHistoryEntry] = []
        self._next = 0

    @property
    def history_id(self) -> str:
        return self._id

    def append(self, message: ModelMessage) -> ChatHistoryEntry:
        entry = ChatHistoryEntry(order=self._next, message=message)
        self._entries.append(entry)
        self._next += 1
        return entry

    def messages(self) -> List[ModelMessage]:
        return [e.message for e in self._entries]

    def __len__(self) -> int:
        return len(self._entries)

    def as_dict(self) -> dict:
        return {
            "history_id": self._id,
            "entries": [e.as_dict() for e in self._entries],
        }
