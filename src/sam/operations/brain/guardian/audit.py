"""
OP-317 — Guardian Audit Integration

Integrasikan dengan Audit Repository yang sudah ada.
Guardian hanya MENULIS audit — tidak boleh mengubah audit.

Catat:
  - gate passed
  - gate rejected
  - policy violation
  - approval waiting
  - approval completed
  - reasoning completed
  - proposal submitted

Append only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class AuditEntry:
    event_type: str
    pipeline_id: str
    detail: str
    timestamp: str = ""
    severity: str = "info"  # info, warning, critical

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type,
            "pipeline_id": self.pipeline_id,
            "detail": self.detail,
            "timestamp": self.timestamp,
            "severity": self.severity,
        }


class GuardianAudit:
    """
    Audit trail untuk guardian.
    Append only — tidak bisa menghapus atau mengubah entry.
    Tidak mengakses audit repository langsung — hanya menulis.
    """

    def __init__(self):
        self._entries: List[AuditEntry] = []
        self._violations: List[str] = []
        self._recommendations: List[str] = []

    # ── Log methods ───────────────────────────────────────────────

    def log_gate_passed(self, pipeline_id: str, gate_result: Any = None) -> AuditEntry:
        entry = AuditEntry(
            event_type="gate_passed",
            pipeline_id=pipeline_id,
            detail=f"Gate passed for pipeline {pipeline_id}",
            timestamp=datetime.now().isoformat(timespec="seconds"),
            severity="info",
        )
        self._entries.append(entry)
        return entry

    def log_gate_rejected(self, pipeline_id: str, rejection: Any = None) -> AuditEntry:
        reason = getattr(rejection, "reason", "unknown") if rejection else "unknown"
        entry = AuditEntry(
            event_type="gate_rejected",
            pipeline_id=pipeline_id,
            detail=f"Gate rejected for pipeline {pipeline_id}: {reason}",
            timestamp=datetime.now().isoformat(timespec="seconds"),
            severity="critical",
        )
        self._entries.append(entry)
        return entry

    def log_policy_violation(self, pipeline_id: str, violation: Any = None) -> AuditEntry:
        message = getattr(violation, "message", "unknown") if violation else "unknown"
        entry = AuditEntry(
            event_type="policy_violation",
            pipeline_id=pipeline_id,
            detail=f"Policy violation for pipeline {pipeline_id}: {message}",
            timestamp=datetime.now().isoformat(timespec="seconds"),
            severity="warning",
        )
        self._entries.append(entry)
        self._violations.append(message)
        return entry

    def log_approval_waiting(self, pipeline_id: str, approval_id: str = "") -> AuditEntry:
        entry = AuditEntry(
            event_type="approval_waiting",
            pipeline_id=pipeline_id,
            detail=f"Approval waiting for pipeline {pipeline_id}: {approval_id}",
            timestamp=datetime.now().isoformat(timespec="seconds"),
            severity="info",
        )
        self._entries.append(entry)
        return entry

    def log_approval_completed(self, pipeline_id: str, approval_id: str = "",
                                approved: bool = False) -> AuditEntry:
        status = "approved" if approved else "rejected"
        entry = AuditEntry(
            event_type="approval_completed",
            pipeline_id=pipeline_id,
            detail=f"Approval {status} for pipeline {pipeline_id}: {approval_id}",
            timestamp=datetime.now().isoformat(timespec="seconds"),
            severity="info",
        )
        self._entries.append(entry)
        return entry

    def log_reasoning_completed(self, pipeline_id: str, summary: str = "") -> AuditEntry:
        entry = AuditEntry(
            event_type="reasoning_completed",
            pipeline_id=pipeline_id,
            detail=f"Reasoning completed for pipeline {pipeline_id}: {summary[:100]}",
            timestamp=datetime.now().isoformat(timespec="seconds"),
            severity="info",
        )
        self._entries.append(entry)
        return entry

    def log_proposal_submitted(self, pipeline_id: str, proposal_id: str = "") -> AuditEntry:
        entry = AuditEntry(
            event_type="proposal_submitted",
            pipeline_id=pipeline_id,
            detail=f"Proposal submitted for pipeline {pipeline_id}: {proposal_id}",
            timestamp=datetime.now().isoformat(timespec="seconds"),
            severity="info",
        )
        self._entries.append(entry)
        return entry

    # ── Query methods ─────────────────────────────────────────────

    def get_entries(self, limit: int = 50) -> Tuple[AuditEntry, ...]:
        return tuple(self._entries[-limit:])

    def get_entries_by_type(self, event_type: str, limit: int = 10) -> Tuple[AuditEntry, ...]:
        matching = [e for e in self._entries if e.event_type == event_type]
        return tuple(matching[-limit:])

    def get_violations(self, limit: int = 10) -> Tuple[str, ...]:
        return tuple(self._violations[-limit:])

    def get_recommendations(self, limit: int = 10) -> Tuple[str, ...]:
        return tuple(self._recommendations[-limit:])

    @property
    def total_entries(self) -> int:
        return len(self._entries)

    def clear(self) -> None:
        """Hanya untuk testing — tidak boleh dipanggil di production."""
        self._entries.clear()
        self._violations.clear()
        self._recommendations.clear()
