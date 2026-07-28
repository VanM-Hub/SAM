"""
Audit — kronologi lengkap dari Decision → Approval → Execution → Verification.

Append-only.
Immutable setelah ditulis.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class AuditEventType(str, Enum):
    DECISION_MADE = "decision_made"
    DECISION_PROPOSED = "decision_proposed"
    APPROVAL_SUBMITTED = "approval_submitted"
    APPROVAL_APPROVED = "approval_approved"
    APPROVAL_REJECTED = "approval_rejected"
    APPROVAL_EXPIRED = "approval_expired"
    APPROVAL_ESCALATED = "approval_escalated"
    EXECUTION_PLAN_CREATED = "execution_plan_created"
    EXECUTION_STARTED = "execution_started"
    EXECUTION_COMPLETED = "execution_completed"
    EXECUTION_FAILED = "execution_failed"
    VERIFICATION_PASSED = "verification_passed"
    VERIFICATION_FAILED = "verification_failed"
    ROLLBACK_STARTED = "rollback_started"
    ROLLBACK_COMPLETED = "rollback_completed"
    ROLLBACK_FAILED = "rollback_failed"
    COMPENSATION_TRIGGERED = "compensation_triggered"
    AUDIT_LOG = "audit_log"
    SYSTEM_EVENT = "system_event"


@dataclass(frozen=True)
class AuditEntry:
    """Satu entri audit — immutable setelah dibuat."""
    id: str
    event_type: AuditEventType
    source_id: str                    # plan_id, decision_id, approval_id
    source_type: str                  # "execution_plan", "decision", "approval", "system"
    title: str
    description: str = ""

    evidence: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)

    actor: str = "system"             # "system", "human", "sam"
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_text(self) -> str:
        lines = [
            "[{}] {}: {}".format(self.timestamp[:19], self.event_type.value, self.title),
            "  Source: {} ({}) | Actor: {}".format(self.source_type, self.source_id, self.actor),
        ]
        if self.description:
            lines.append("  Detail: {}".format(self.description))
        if self.evidence:
            for e in self.evidence[:3]:
                lines.append("  Evidence: {}".format(e))
        return "\n".join(lines)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "event_type": self.event_type.value,
            "source_id": self.source_id,
            "source_type": self.source_type,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "metadata": self.metadata,
            "actor": self.actor,
            "timestamp": self.timestamp,
        }


class AuditTrail:
    """Audit trail — append-only, immutable.

    Tidak bisa:
    - Menghapus entri
    - Mengedit entri
    - Memasukkan entri di tengah
    """

    def __init__(self, max_entries: int = 10000):
        self._entries: List[AuditEntry] = []
        self._max_entries = max_entries
        self._counter: int = 0

    def record(self, event_type: AuditEventType, source_id: str,
               source_type: str, title: str,
               description: str = "",
               evidence: List[str] = None,
               metadata: Dict[str, Any] = None,
               actor: str = "system") -> AuditEntry:
        """Catat entri baru — append-only."""
        self._counter += 1
        entry = AuditEntry(
            id="aud-{:05d}".format(self._counter),
            event_type=event_type,
            source_id=source_id,
            source_type=source_type,
            title=title,
            description=description,
            evidence=evidence or [],
            metadata=metadata or {},
            actor=actor,
        )
        self._entries.append(entry)

        # Truncate if exceeds max
        if len(self._entries) > self._max_entries:
            self._entries = self._entries[-self._max_entries:]

        return entry

    def get_by_source(self, source_id: str) -> List[AuditEntry]:
        """Entri untuk satu source (plan/decision/approval)."""
        return [e for e in self._entries if e.source_id == source_id]

    def get_by_type(self, event_type: AuditEventType) -> List[AuditEntry]:
        """Entri berdasarkan tipe."""
        return [e for e in self._entries if e.event_type == event_type]

    def get_recent(self, limit: int = 20) -> List[AuditEntry]:
        """Entri terbaru."""
        return self._entries[-limit:]

    def get_timeline(self, source_id: str = "") -> str:
        """Kronologi untuk satu source atau semua."""
        entries = self.get_by_source(source_id) if source_id else self._entries
        if not entries:
            return "No audit entries."

        lines = []
        for e in entries:
            lines.append(e.to_text())
        return "\n".join(lines)

    def count(self) -> int:
        return len(self._entries)

    def clear(self):
        """Hapus semua — hanya untuk testing.

        Deprecated: Audit tidak boleh mutable untuk production.
        Gunakan SQLite AuditRepository untuk persist audit.
        """
        import warnings
        warnings.warn(
            "AuditTrail.clear() is deprecated. Use SQLite AuditRepository for production audit.",
            DeprecationWarning, stacklevel=2
        )
        self._entries = []
        self._counter = 0


# Singleton audit trail
_audit_instance: Optional[AuditTrail] = None


def get_audit_trail() -> AuditTrail:
    """Dapatkan instance audit trail (singleton internal)."""
    global _audit_instance
    if _audit_instance is None:
        _audit_instance = AuditTrail()
    return _audit_instance
