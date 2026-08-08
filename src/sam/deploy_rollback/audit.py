"""
Deployment Rollback — Audit.

Jejak auditable operasi deployment & rollback: deploy, activate, rollback,
verifikasi. Hanya metadata (artifact_id, version, event, outcome, reason,
timestamp) — TIDAK menyimpan payload state deployment. Mendukung
accountability rollback deployment.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List

from datetime import datetime, timezone


def _utcnow_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class DeploymentAuditRecord:
    """Satu catatan audit deployment/rollback (immutable)."""

    record_id: int
    event: str  # deploy | activate | rollback | verify
    outcome: str  # success | failure
    artifact_id: str = ""
    version: str = ""
    reason: str = ""
    timestamp: str = field(default_factory=_utcnow_iso)

    def as_dict(self) -> Dict[str, str]:
        return {
            "record_id": str(self.record_id),
            "event": self.event,
            "outcome": self.outcome,
            "artifact_id": self.artifact_id,
            "version": self.version,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


class DeploymentAuditLog:
    """Append-only ring buffer audit operasi deployment/rollback."""

    def __init__(self, max_records: int = 500) -> None:
        self._max = max_records
        self._records: List[DeploymentAuditRecord] = []
        self._seq = 0

    def record(
        self,
        event: str,
        outcome: str,
        artifact_id: str = "",
        version: str = "",
        reason: str = "",
    ) -> None:
        self._seq += 1
        rec = DeploymentAuditRecord(
            record_id=self._seq,
            event=event,
            outcome=outcome,
            artifact_id=artifact_id,
            version=version,
            reason=reason,
        )
        self._records.append(rec)
        if len(self._records) > self._max:
            self._records = self._records[-self._max:]

    def all(self) -> List[DeploymentAuditRecord]:
        return list(self._records)

    def count(self) -> int:
        return len(self._records)

    def failures(self) -> List[DeploymentAuditRecord]:
        return [r for r in self._records if r.outcome == "failure"]

    def by_artifact(self, artifact_id: str) -> List[DeploymentAuditRecord]:
        return [r for r in self._records if r.artifact_id == artifact_id]
