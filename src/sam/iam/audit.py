"""IAM Audit — catatan akses user (menutup sebagian D5-G4).

Mencatat peristiwa autentikasi + otorisasi (sukses/gagal) untuk accountability.
TIDAK menyimpan kredensial. Menyediakan jalur audit yang bisa dikonsumsi
operasional (print/log/stream), tanpa mengubah runtime existing.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List, Optional


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AccessAuditRecord:
    """Satu rekaman audit akses (immutable)."""

    record_id: int
    event: str          # authenticate | authorize
    outcome: str        # success | failure
    username: str = ""
    principal_id: str = ""
    resource: str = ""
    action: str = ""
    reason: str = ""
    timestamp: str = field(default_factory=_utcnow)

    def as_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "event": self.event,
            "outcome": self.outcome,
            "username": self.username,
            "principal_id": self.principal_id,
            "resource": self.resource,
            "action": self.action,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class AccessAuditLog:
    """Append-only log audit akses user (in-memory)."""

    def __init__(self, max_records: int = 1000) -> None:
        self._records: List[AccessAuditRecord] = []
        self._max = max_records
        self._seq = 0

    def record(
        self,
        event: str,
        outcome: str,
        username: str = "",
        principal_id: str = "",
        resource: str = "",
        action: str = "",
        reason: str = "",
    ) -> AccessAuditRecord:
        self._seq += 1
        rec = AccessAuditRecord(
            record_id=self._seq,
            event=event,
            outcome=outcome,
            username=username,
            principal_id=principal_id,
            resource=resource,
            action=action,
            reason=reason,
        )
        self._records.append(rec)
        # ring buffer: buang rekaman tertua bila melebihi kapasitas
        if len(self._records) > self._max:
            self._records = self._records[-self._max:]
        return rec

    def all(self) -> List[AccessAuditRecord]:
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def failures(self) -> List[AccessAuditRecord]:
        return [r for r in self._records if r.outcome == "failure"]
