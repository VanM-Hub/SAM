"""Conversation Model - WP-21 (MISSION-5.1 / IP-5.1-003).

Domain model conversation universal. Identity stabil dan dapat ditelusuri.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Tuple


class ConversationStatus(str, Enum):
    """Status siklus hidup conversation."""

    OPEN = "open"
    PAUSED = "paused"
    CLOSED = "closed"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class Conversation:
    """Sebuah conversation (identitas stabil)."""

    conversation_id: str
    title: str = ""
    participant: str = ""
    status: ConversationStatus = ConversationStatus.OPEN
    provider_context: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "conversation_id": self.conversation_id,
            "title": self.title,
            "participant": self.participant,
            "status": self.status.value,
            "provider_context": dict(self.provider_context),
            "created_at": self.created_at,
        }
