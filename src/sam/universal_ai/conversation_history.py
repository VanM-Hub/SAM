"""Conversation History - WP-27 (MISSION-5.1 / IP-5.1-003).

Persistence terhadap conversation history dengan preservation provenance.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional, Tuple

from .message_model import Message


@dataclass(frozen=True)
class HistoryPage:
    """Hasil pagination history."""

    items: Tuple[Message, ...]
    total: int
    offset: int
    limit: int

    def as_dict(self) -> dict:
        return {
            "items": [m.as_dict() for m in self.items],
            "total": self.total,
            "offset": self.offset,
            "limit": self.limit,
        }


class ConversationHistoryStore:
    """Menyimpan dan mengambil riwayat pesan conversation."""

    def __init__(self) -> None:
        self._messages: List[Message] = []

    def append(self, message: Message) -> None:
        self._messages.append(message)

    def append_many(self, messages: Tuple[Message, ...]) -> None:
        self._messages.extend(messages)

    def history(self, conversation_id: str) -> Tuple[Message, ...]:
        return tuple(m for m in self._messages if m.conversation_id == conversation_id)

    def session_history(self, session_id: str) -> Tuple[Message, ...]:
        return tuple(m for m in self._messages if m.session_id == session_id)

    def page(
        self,
        conversation_id: str,
        *,
        offset: int = 0,
        limit: int = 50,
        role_filter: Optional[str] = None,
    ) -> HistoryPage:
        items = self.history(conversation_id)
        if role_filter:
            items = tuple(m for m in items if m.role.value == role_filter)
        total = len(items)
        sliced = items[offset : offset + limit]
        return HistoryPage(items=sliced, total=total, offset=offset, limit=limit)
