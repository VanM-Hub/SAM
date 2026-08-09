"""Execution Audit - IP-4.1-001 WP-08.

Provider Execution Foundation.
Mencatat seluruh aktivitas execution secara deterministik.

Scope (Foundation immutable, Article XI - Audit Everything):
- Seluruh execution menghasilkan audit.
- Timeline lengkap tersedia (request -> approval -> dispatch -> provider -> response).
- Audit immutable (Article VI).
- Audit dapat diverifikasi.
- Audit API (read-only).

Tidak ada network, tidak ada authority. Catatan append-only, no mutation.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Optional, Tuple


# ---------------------------------------------------------------------------
# Model (immutable)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class AuditTimelineStep:
    """Satu langkah timeline audit (immutable)."""

    stage: str            # request | validation | approval | dispatch | provider | response | report
    status: str
    detail: str = ""
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"stage": self.stage, "status": self.status,
                "detail": self.detail, "external_calls": self.external_calls}


@dataclass(frozen=True)
class ExecutionAuditRecord:
    """Satu record audit eksekusi (immutable)."""

    audit_id: str
    execution_id: str
    provider_id: str
    operation: str
    mode: str
    status: str
    hash: str                              # hash deterministik untuk verifikasi integritas
    timeline: Tuple[AuditTimelineStep, ...] = field(default_factory=tuple)
    approver: str = ""
    approval_id: str = ""
    recorded_at: str = ""

    def as_dict(self) -> dict:
        return {
            "audit_id": self.audit_id,
            "execution_id": self.execution_id,
            "provider_id": self.provider_id,
            "operation": self.operation,
            "mode": self.mode,
            "status": self.status,
            "hash": self.hash,
            "timeline": [t.as_dict() for t in self.timeline],
            "approver": self.approver,
            "approval_id": self.approval_id,
            "recorded_at": self.recorded_at,
        }


@dataclass(frozen=True)
class AuditSummary:
    """Ringkasan audit (immutable)."""

    total: int
    executed: int
    blocked: int
    preview: int
    by_status: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {"total": self.total, "executed": self.executed,
                "blocked": self.blocked, "preview": self.preview,
                "by_status": dict(self.by_status)}


# ---------------------------------------------------------------------------
# Hash deterministik (integritas)
# ---------------------------------------------------------------------------


def _canonical(timeline: Tuple[AuditTimelineStep, ...]) -> str:
    parts = ["{}|{}|{}|{}".format(t.stage, t.status, t.detail, t.external_calls)
             for t in timeline]
    return "|".join(parts)


def audit_hash(execution_id: str, provider_id: str, operation: str, mode: str,
               status: str, timeline: Tuple[AuditTimelineStep, ...]) -> str:
    """Hash deterministik dari isi audit (Article VII)."""
    payload = "{}~{}~{}~{}~{}~{}".format(
        execution_id, provider_id, operation, mode, status, _canonical(timeline),
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------
# Audit trail (append-only)
# ---------------------------------------------------------------------------


class ExecutionAudit:
    """Audit trail eksekusi (append-only, immutable, verifiable)."""

    def __init__(self) -> None:
        self._records: Dict[str, ExecutionAuditRecord] = {}

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def record(
        self,
        execution_id: str,
        provider_id: str,
        operation: str,
        mode: str,
        status: str,
        timeline: Tuple[AuditTimelineStep, ...],
        approver: str = "",
        approval_id: str = "",
    ) -> ExecutionAuditRecord:
        if execution_id in self._records:
            return self._records[execution_id]  # idempotent, tidak duplikasi
        record_id = "aud-{}-{}".format(execution_id, len(self._records))
        rec = ExecutionAuditRecord(
            audit_id=record_id,
            execution_id=execution_id,
            provider_id=provider_id,
            operation=operation,
            mode=mode,
            status=status,
            hash=audit_hash(execution_id, provider_id, operation, mode, status, timeline),
            timeline=timeline,
            approver=approver,
            approval_id=approval_id,
            recorded_at=self._now(),
        )
        self._records[execution_id] = rec
        return rec

    def get(self, execution_id: str) -> Optional[ExecutionAuditRecord]:
        return self._records.get(execution_id)

    def all(self) -> Tuple[ExecutionAuditRecord, ...]:
        return tuple(self._records.values())

    def verify(self, execution_id: str) -> bool:
        """Verifikasi integritas record: hash harus cocok (deterministik)."""
        rec = self._records.get(execution_id)
        if rec is None:
            return False
        expected = audit_hash(rec.execution_id, rec.provider_id, rec.operation,
                              rec.mode, rec.status, rec.timeline)
        return expected == rec.hash

    def summary(self) -> AuditSummary:
        recs = self._records.values()
        by = {}  # type: Dict[str, int]
        for r in recs:
            by[r.status] = by.get(r.status, 0) + 1
        return AuditSummary(
            total=len(recs),
            executed=sum(1 for r in recs if r.mode == "execute" and r.status == "completed"),
            blocked=sum(1 for r in recs if r.status == "blocked"),
            preview=sum(1 for r in recs if r.mode == "preview"),
            by_status=by,
        )

    def clear(self) -> None:
        self._records.clear()
