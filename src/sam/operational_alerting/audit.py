"""
Operational Alerting — Audit (metadata-only).

Mencatat event alert operational (route/dedup/acknowledge/resolve) tanpa
menyimpan payload/state alert. Konsisten pola audit H2/H3: metadata, ring
buffer, ikut class untuk observability.

Tidak menyimpan rahasia. Tidak melakukan efek eksternal.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from .state import AlertSeverity, _utcnow_iso


@dataclass(frozen=True)
class AlertAuditRecord:
    """Satu jejak audit event alert (metadata)."""

    event: str  # route | dedup | acknowledge | resolve
    alert_id: str
    severity: str
    source: str = ""
    outcome: str = ""  # success | skipped | rejected
    operator: str = ""
    timestamp: str = field(default_factory=_utcnow_iso)

    def as_dict(self) -> Dict[str, Any]:
        return {
            "event": self.event,
            "alert_id": self.alert_id,
            "severity": self.severity,
            "source": self.source,
            "outcome": self.outcome,
            "operator": self.operator,
            "timestamp": self.timestamp,
        }


class AlertAuditLog:
    """Ring buffer jejak audit event alert (metadata only)."""

    def __init__(self, max_records: int = 500) -> None:
        self._max = max(max_records, 1)
        self._records: List[AlertAuditRecord] = []

    def record(
        self,
        event: str,
        alert_id: str,
        severity: AlertSeverity,
        source: str = "",
        outcome: str = "success",
        operator: str = "",
    ) -> None:
        if isinstance(severity, str):
            severity = AlertSeverity(severity)
        self._records.append(
            AlertAuditRecord(
                event=event,
                alert_id=alert_id,
                severity=severity.value,
                source=source,
                outcome=outcome,
                operator=operator,
            )
        )
        if len(self._records) > self._max:
            self._records = self._records[-self._max:]

    def all(self) -> List[AlertAuditRecord]:
        return list(self._records)

    def by_event(self, event: str) -> List[AlertAuditRecord]:
        return [r for r in self._records if r.event == event]

    def failures(self) -> List[AlertAuditRecord]:
        return [r for r in self._records if r.outcome != "success"]

    def count(self) -> int:
        return len(self._records)
