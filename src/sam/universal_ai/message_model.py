"""Message Model - WP-23 (MISSION-5.1 / IP-5.1-003).

Model pesan universal yang mempertahankan provenance: user message, system
context, governance context, assistant response, tool-related context, evidence
reference.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Tuple


class MessageRole(str, Enum):
    """Peran pesan dalam conversation."""

    USER = "user"
    SYSTEM_CONTEXT = "system_context"
    GOVERNANCE_CONTEXT = "governance_context"
    ASSISTANT = "assistant"
    TOOL_CONTEXT = "tool_context"
    EVIDENCE_REFERENCE = "evidence_reference"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class Message:
    """Sebuah pesan universal dengan provenance."""

    message_id: str
    role: MessageRole
    content: str
    conversation_id: str = ""
    session_id: str = ""
    evidence_refs: Tuple[str, ...] = field(default_factory=tuple)
    created_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "message_id": self.message_id,
            "role": self.role.value,
            "content": self.content,
            "conversation_id": self.conversation_id,
            "session_id": self.session_id,
            "evidence_refs": list(self.evidence_refs),
            "created_at": self.created_at,
        }
