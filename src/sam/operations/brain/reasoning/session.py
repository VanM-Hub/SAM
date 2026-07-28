"""
OP-291 — Reasoning Session Manager

Mengelola siklus hidup sesi reasoning.
Tidak memanggil provider. Murni state management.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Optional, List, Dict, Tuple
from datetime import datetime
import copy


@dataclass(frozen=True)
class ReasoningContext:
    """Konteks reasoning untuk satu permintaan."""
    operator_question: str
    conversation_summary: str = ""
    mission_summary: str = ""
    timeline_summary: str = ""
    observation_summary: str = ""
    health_summary: str = ""
    trust_summary: str = ""
    evidence_ids: Tuple[str, ...] = ()
    template_name: str = ""
    system_prompt: str = ""
    token_estimate: int = 0
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "operator_question": self.operator_question,
            "conversation_summary": self.conversation_summary,
            "mission_summary": self.mission_summary,
            "timeline_summary": self.timeline_summary,
            "observation_summary": self.observation_summary,
            "health_summary": self.health_summary,
            "trust_summary": self.trust_summary,
            "evidence_ids": list(self.evidence_ids),
            "template_name": self.template_name,
            "token_estimate": self.token_estimate,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class SessionSnapshot:
    """Snapshot sesi pada satu titik waktu."""
    session_id: str
    reasoning_count: int
    context: ReasoningContext
    tokens_used: int
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "reasoning_count": self.reasoning_count,
            "context": self.context.to_dict(),
            "tokens_used": self.tokens_used,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class ReasoningRecord:
    """Satu record reasoning dalam sesi."""
    record_id: str
    operator_question: str
    template_name: str
    token_estimate: int
    response_preview: str
    confidence: float
    timestamp: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "record_id": self.record_id,
            "operator_question": self.operator_question,
            "template_name": self.template_name,
            "token_estimate": self.token_estimate,
            "response_preview": self.response_preview,
            "confidence": self.confidence,
            "timestamp": self.timestamp,
        }


class ReasoningHistory:
    """Riwayat reasoning dalam sesi."""
    def __init__(self, max_records: int = 50):
        self._records: List[ReasoningRecord] = []
        self._max_records = max_records

    @property
    def count(self) -> int:
        return len(self._records)

    @property
    def records(self) -> Tuple[ReasoningRecord, ...]:
        return tuple(self._records)

    def add(self, record: ReasoningRecord) -> None:
        self._records.append(record)
        if len(self._records) > self._max_records:
            self._records.pop(0)

    def clear(self) -> None:
        self._records.clear()

    def latest(self, n: int = 1) -> Tuple[ReasoningRecord, ...]:
        if n <= 0:
            return ()
        return tuple(self._records[-n:])

    def query_by_template(self, template_name: str) -> Tuple[ReasoningRecord, ...]:
        return tuple(r for r in self._records if r.template_name == template_name)

    def total_tokens(self) -> int:
        return sum(r.token_estimate for r in self._records)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "records": [r.to_dict() for r in self._records],
            "total_tokens": self.total_tokens(),
        }


class ReasoningSession:
    """
    Satu sesi reasoning.
    Mengelola lifecycle, conversation memory, context window.
    Tidak memanggil provider — murni state management.
    """
    def __init__(self, session_id: str = ""):
        self._session_id = session_id or f"rs-{int(datetime.now().timestamp())}"
        self._history = ReasoningHistory()
        self._current_context: Optional[ReasoningContext] = None
        self._tokens_used = 0
        self._created_at = datetime.now().isoformat(timespec="seconds")
        self._is_active = True

    @property
    def session_id(self) -> str:
        return self._session_id

    @property
    def is_active(self) -> bool:
        return self._is_active

    @property
    def history(self) -> ReasoningHistory:
        return self._history

    @property
    def current_context(self) -> Optional[ReasoningContext]:
        return self._current_context

    @property
    def tokens_used(self) -> int:
        return self._tokens_used

    @property
    def reasoning_count(self) -> int:
        return self._history.count

    @property
    def created_at(self) -> str:
        return self._created_at

    def set_context(self, context: ReasoningContext) -> None:
        if not self._is_active:
            raise RuntimeError("Session is closed")
        self._current_context = context

    def record_reasoning(self, question: str, template_name: str,
                         token_estimate: int = 0,
                         response_preview: str = "",
                         confidence: float = 1.0) -> ReasoningRecord:
        if not self._is_active:
            raise RuntimeError("Session is closed")
        record = ReasoningRecord(
            record_id=f"rec-{self._history.count + 1}-{int(datetime.now().timestamp())}",
            operator_question=question,
            template_name=template_name,
            token_estimate=token_estimate,
            response_preview=response_preview[:200],
            confidence=min(max(confidence, 0.0), 1.0),
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
        self._history.add(record)
        self._tokens_used += token_estimate
        return record

    def reset(self) -> None:
        """Reset session: hapus history, reset tokens."""
        self._history.clear()
        self._current_context = None
        self._tokens_used = 0

    def close(self) -> None:
        """Tutup session. Tidak bisa digunakan lagi."""
        self._is_active = False

    def snapshot(self) -> SessionSnapshot:
        """Ambil snapshot sesi saat ini."""
        return SessionSnapshot(
            session_id=self._session_id,
            reasoning_count=self.reasoning_count,
            context=self._current_context or ReasoningContext(
                operator_question="(no context)",
            ),
            tokens_used=self._tokens_used,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )

    def export(self) -> Dict[str, Any]:
        """Export sesi ke dict (serializable)."""
        return {
            "session_id": self._session_id,
            "is_active": self._is_active,
            "reasoning_count": self.reasoning_count,
            "tokens_used": self._tokens_used,
            "created_at": self._created_at,
            "history": self._history.to_dict(),
            "current_context": self._current_context.to_dict()
            if self._current_context else None,
        }

    @staticmethod
    def estimate_tokens(text: str) -> int:
        """Estimasi token: ~4 chars per token."""
        if not text:
            return 0
        return len(text) // 4 + 1
