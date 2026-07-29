# OP-425 — Dispatch Audit
# Python 3.8, frozen DTO, synchronous

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any, Tuple
import uuid


AUDIT_ACTIONS = (
    "created", "validated", "approved", "queued",
    "cancelled", "previewed",
)


@dataclass(frozen=True)
class DispatchAuditEntry:
    entry_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    request_id: str = ""
    action: str = ""  # created, validated, approved, queued, cancelled, previewed
    details: str = ""
    timestamp: datetime = field(default_factory=datetime.utcnow)
    actor: str = "system"


@dataclass(frozen=True)
class DispatchAuditSummary:
    total_entries: int = 0
    by_action: Dict[str, int] = field(default_factory=dict)
    first_entry: Optional[datetime] = None
    last_entry: Optional[datetime] = None


class DispatchAudit:
    """Audit trail for dispatch operations.

    Records actions without execution logs:
    created, validated, approved, queued, cancelled, previewed
    """

    def __init__(self) -> None:
        self._entries: List[DispatchAuditEntry] = []

    def record(
        self,
        request_id: str,
        action: str,
        details: str = "",
        actor: str = "system",
    ) -> DispatchAuditEntry:
        """Record an audit entry."""
        entry = DispatchAuditEntry(
            request_id=request_id,
            action=action,
            details=details or f"Dispatch {action}",
            actor=actor,
        )
        self._entries.append(entry)
        return entry

    def get_entries(
        self,
        request_id: Optional[str] = None,
        action: Optional[str] = None,
        limit: int = 50,
    ) -> Tuple[DispatchAuditEntry, ...]:
        """Get audit entries with optional filters."""
        results = list(self._entries)

        if request_id:
            results = [e for e in results if e.request_id == request_id]
        if action:
            results = [e for e in results if e.action == action]

        # Sort by timestamp descending
        results.sort(key=lambda e: e.timestamp, reverse=True)

        return tuple(results[:limit])

    def get_summary(self) -> DispatchAuditSummary:
        """Get audit summary statistics."""
        by_action: Dict[str, int] = {}
        for e in self._entries:
            by_action[e.action] = by_action.get(e.action, 0) + 1

        timestamps = [e.timestamp for e in self._entries]
        first = min(timestamps) if timestamps else None
        last = max(timestamps) if timestamps else None

        return DispatchAuditSummary(
            total_entries=len(self._entries),
            by_action=by_action,
            first_entry=first,
            last_entry=last,
        )

    def get_actions(self) -> Tuple[str, ...]:
        return AUDIT_ACTIONS

    def clear(self) -> None:
        self._entries.clear()
