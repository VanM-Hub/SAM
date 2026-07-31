"""Chat Summary — ringkasan sesi chat (Sprint 241).

Program B — Model Runtime Integration.
Read-only, deterministik, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .chat_history import ChatHistory


@dataclass(frozen=True)
class ChatSummary:
    """Ringkasan chat (immutable)."""
    session_id: str
    total_messages: int = 0
    role_counts: Dict[str, int] = field(default_factory=dict)
    estimated_tokens: int = 0
    preview_only: bool = True

    def as_dict(self) -> dict:
        return {
            "session_id": self.session_id,
            "total_messages": self.total_messages,
            "role_counts": dict(self.role_counts),
            "estimated_tokens": self.estimated_tokens,
            "preview_only": self.preview_only,
        }


class ChatSummarizer:
    """Merangkum riwayat chat. Read-only, no-network."""

    def summarize(self, history: ChatHistory) -> ChatSummary:
        counts: Dict[str, int] = {}
        tokens = 0
        for entry in history.as_dict()["entries"]:
            role = entry["message"]["role"]
            counts[role] = counts.get(role, 0) + 1
            tokens += len(entry["message"]["content"].split()) + 4
        return ChatSummary(
            session_id=history.history_id,
            total_messages=len(history),
            role_counts=counts,
            estimated_tokens=tokens,
            preview_only=True,
        )
