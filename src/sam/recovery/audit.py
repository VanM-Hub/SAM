"""Recovery Audit — catatan operasi checkpoint & restore.

Menyediakan jejak auditable: siapa/menunjukkan kemajuan, kapan checkpoint
dibuat/dihapus/direstore, dan apakah restore sukses/gagal. Tidak menyimpan
payload state (hanya metadata). Mendukung accountability recovery.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import List


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class CheckpointAuditRecord:
    """Satu rekaman audit recovery (immutable, tanpa payload state)."""

    record_id: int
    event: str          # checkpoint_create | checkpoint_delete | restore
    outcome: str        # success | failure
    scope: str = ""
    checkpoint_id: str = ""
    reason: str = ""
    timestamp: str = field(default_factory=_utcnow_iso)

    def as_dict(self) -> dict:
        return {
            "record_id": self.record_id,
            "event": self.event,
            "outcome": self.outcome,
            "scope": self.scope,
            "checkpoint_id": self.checkpoint_id,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class CheckpointAuditLog:
    """Append-only log audit recovery (in-memory, ring buffer)."""

    def __init__(self, max_records: int = 500) -> None:
        self._records: List[CheckpointAuditRecord] = []
        self._max = max_records
        self._seq = 0

    def record(self, event: str, outcome: str, scope: str = "",
               checkpoint_id: str = "", reason: str = "") -> CheckpointAuditRecord:
        self._seq += 1
        rec = CheckpointAuditRecord(
            record_id=self._seq, event=event, outcome=outcome,
            scope=scope, checkpoint_id=checkpoint_id, reason=reason,
        )
        self._records.append(rec)
        if len(self._records) > self._max:
            self._records = self._records[-self._max:]
        return rec

    def all(self) -> List[CheckpointAuditRecord]:
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def failures(self) -> List[CheckpointAuditRecord]:
        return [r for r in self._records if r.outcome == "failure"]
