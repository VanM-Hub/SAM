"""Dashboard Chat — bridge dashboard <-> model chat (Sprint 241).

Program B — Model Runtime Integration.
Read-only bridge; preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List

from .chat_summary import ChatSummary, ChatSummarizer
from .chat_session import ChatSessionStore


@dataclass(frozen=True)
class DashboardChatRow:
    """Satu baris chat pada dashboard (immutable)."""
    row_id: str
    session_id: str
    total_messages: int = 0
    preview_only: bool = True

    def as_dict(self) -> dict:
        return {
            "row_id": self.row_id,
            "session_id": self.session_id,
            "total_messages": self.total_messages,
            "preview_only": self.preview_only,
        }


class DashboardChat:
    """Bridge dashboard <-> chat. Read-only, no-network."""

    def __init__(self, store: ChatSessionStore | None = None) -> None:
        self._store = store or ChatSessionStore()
        self._summarizer = ChatSummarizer()

    def rows(self) -> List[DashboardChatRow]:
        out = []
        for session_id in [s[0].session_id for s in self._store._sessions.values()]:
            hist = self._store.history(session_id)
            out.append(DashboardChatRow(
                row_id=f"dchat-{session_id}",
                session_id=session_id,
                total_messages=len(hist),
                preview_only=True,
            ))
        return out

    def summary(self) -> Dict[str, object]:
        rows = self.rows()
        total = sum(r.total_messages for r in rows)
        return {
            "sessions": len(rows),
            "total_messages": total,
            "external_calls": 0,
        }
