"""Operational Histories - WP-04/05/06 (MISSION-4.3 / IP-4.3-001).

Menyimpan seluruh riwayat investigasi, eksekusi, dan verifikasi operasional.
Setiap history tersimpan persisten, dapat ditelusuri & dicari, auditable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional, Tuple

from .persistent_storage import PersistenceEngine


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


class HistoryKind:
    INVESTIGATION = "investigation"
    EXECUTION = "execution"
    VERIFICATION = "verification"

    _VALID = (INVESTIGATION, EXECUTION, VERIFICATION)

    @classmethod
    def valid(cls, kind: str) -> bool:
        return kind in cls._VALID


@dataclass(frozen=True)
class HistoryRecord:
    """Satu catatan history (immutable)."""

    record_id: str
    kind: str
    summary: str
    timeline: Tuple[Tuple[str, str], ...] = field(default_factory=tuple)
    result: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    evidence_ids: Tuple[str, ...] = field(default_factory=tuple)
    recorded_at: str = field(default_factory=_now_utc)

    def as_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "kind": self.kind,
            "summary": self.summary,
            "timeline": [list(t) for t in self.timeline],
            "result": self.result,
            "metadata": self.metadata,
            "evidence_ids": list(self.evidence_ids),
            "recorded_at": self.recorded_at,
        }


class HistoryStore:
    """Penyimpanan history (append-only, persisten)."""

    def __init__(self, engine: PersistenceEngine) -> None:
        self._engine = engine

    def save(self, record: HistoryRecord) -> None:
        self._engine.append(record.record_id, record.as_dict())

    def get(self, record_id: str) -> Optional[HistoryRecord]:
        rec = self._engine.get(record_id)
        if rec is None:
            return None
        payload = dict(rec.payload)
        return self._from_dict(payload)

    def all(self, kind: Optional[str] = None) -> Tuple[HistoryRecord, ...]:
        records = [
            self._from_dict(dict(r.payload))
            for r in self._engine.all()
        ]
        if kind:
            records = [r for r in records if r.kind == kind]
        return tuple(records)

    def search(self, *, kind: Optional[str] = None, query: str = "") -> Tuple[HistoryRecord, ...]:
        records = self.all(kind)
        if not query:
            return records
        q = query.lower()
        return tuple(
            r for r in records if q in r.summary.lower()
        )

    def count(self, kind: Optional[str] = None) -> int:
        return len(self.all(kind))

    @staticmethod
    def _from_dict(payload: Dict[str, Any]) -> HistoryRecord:
        return HistoryRecord(
            record_id=payload["record_id"],
            kind=payload.get("kind", ""),
            summary=payload.get("summary", ""),
            timeline=tuple(tuple(x) for x in payload.get("timeline") or ()),
            result=payload.get("result") or {},
            metadata=payload.get("metadata") or {},
            evidence_ids=tuple(payload.get("evidence_ids") or ()),
            recorded_at=payload.get("recorded_at", ""),
        )


# --- Convenience builders per kind ---

class InvestigationHistory:
    """Riwayat investigasi (WP-04)."""

    def __init__(self, store: HistoryStore) -> None:
        self._store = store

    def record(
        self,
        investigation_id: str,
        summary: str,
        timeline: Tuple[Tuple[str, str], ...] = (),
        evidence_ids: Tuple[str, ...] = (),
    ) -> HistoryRecord:
        record = HistoryRecord(
            record_id=investigation_id,
            kind=HistoryKind.INVESTIGATION,
            summary=summary,
            timeline=timeline,
            evidence_ids=evidence_ids,
        )
        self._store.save(record)
        return record

    def get(self, investigation_id: str) -> Optional[HistoryRecord]:
        return self._store.get(investigation_id)

    def all(self) -> Tuple[HistoryRecord, ...]:
        return self._store.all(HistoryKind.INVESTIGATION)

    def search(self, query: str = "") -> Tuple[HistoryRecord, ...]:
        return self._store.search(kind=HistoryKind.INVESTIGATION, query=query)


class ExecutionHistory:
    """Riwayat eksekusi (WP-05) - approval & audit terhubung via metadata."""

    def __init__(self, store: HistoryStore) -> None:
        self._store = store

    def record(
        self,
        execution_id: str,
        summary: str,
        *,
        approval_id: str = "",
        audit_id: str = "",
        outcome: str = "",
        evidence_ids: Tuple[str, ...] = (),
        timeline: Tuple[Tuple[str, str], ...] = (),
    ) -> HistoryRecord:
        record = HistoryRecord(
            record_id=execution_id,
            kind=HistoryKind.EXECUTION,
            summary=summary,
            metadata={
                "approval_id": approval_id,
                "audit_id": audit_id,
                "outcome": outcome,
            },
            evidence_ids=evidence_ids,
            timeline=timeline,
        )
        self._store.save(record)
        return record

    def get(self, execution_id: str) -> Optional[HistoryRecord]:
        return self._store.get(execution_id)

    def all(self) -> Tuple[HistoryRecord, ...]:
        return self._store.all(HistoryKind.EXECUTION)

    def search(self, query: str = "") -> Tuple[HistoryRecord, ...]:
        return self._store.search(kind=HistoryKind.EXECUTION, query=query)


class VerificationHistory:
    """Riwayat verifikasi (WP-06)."""

    def __init__(self, store: HistoryStore) -> None:
        self._store = store

    def record(
        self,
        verification_id: str,
        summary: str,
        *,
        result: Dict[str, Any] = None,
        evidence_ids: Tuple[str, ...] = (),
        timeline: Tuple[Tuple[str, str], ...] = (),
    ) -> HistoryRecord:
        record = HistoryRecord(
            record_id=verification_id,
            kind=HistoryKind.VERIFICATION,
            summary=summary,
            result=result or {},
            evidence_ids=evidence_ids,
            timeline=timeline,
        )
        self._store.save(record)
        return record

    def get(self, verification_id: str) -> Optional[HistoryRecord]:
        return self._store.get(verification_id)

    def all(self) -> Tuple[HistoryRecord, ...]:
        return self._store.all(HistoryKind.VERIFICATION)

    def search(self, query: str = "") -> Tuple[HistoryRecord, ...]:
        return self._store.search(kind=HistoryKind.VERIFICATION, query=query)
