"""
OP-333 — Guardian History

In-memory event history.
Tidak menggunakan repository/storage — ring buffer murni.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════
# DTOs
# ══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GuardianEvent:
    """Satu event dalam history."""
    event_id: str = ""
    category: str = "info"
    severity: str = "low"
    message: str = ""
    detail: str = ""
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_id": self.event_id,
            "category": self.category,
            "severity": self.severity,
            "message": self.message,
            "detail": self.detail,
            "timestamp": self.timestamp,
        }


@dataclass(frozen=True)
class GuardianTimeline:
    """Timeline dari kumpulan event."""
    events: Tuple[GuardianEvent, ...] = field(default_factory=tuple)
    source: str = "guardian"

    @property
    def count(self) -> int:
        return len(self.events)


# ══════════════════════════════════════════════════════════════════════
# History Service
# ══════════════════════════════════════════════════════════════════════

class GuardianHistoryService:
    """In-memory event history dengan filter."""

    MAX_EVENTS = 200

    def __init__(self, max_events: int = MAX_EVENTS):
        self._events: List[GuardianEvent] = []
        self._max = max_events
        self._counter = 0

    @property
    def event_count(self) -> int:
        return len(self._events)

    @property
    def all_events(self) -> Tuple[GuardianEvent, ...]:
        return tuple(self._events)

    def append(self, event: GuardianEvent) -> None:
        """Tambahkan event. Jika melebihi MAX, hapus yang tertua."""
        self._events.append(event)
        if len(self._events) > self._max:
            self._events.pop(0)

    def append_event(
        self, category: str = "info", severity: str = "low",
        message: str = "", detail: str = "",
    ) -> GuardianEvent:
        """Buat event dan append."""
        self._counter += 1
        event = GuardianEvent(
            event_id="evt-{}-{}".format(
                datetime.now().strftime("%H%M%S"), self._counter,
            ),
            category=category,
            severity=severity,
            message=message,
            detail=detail,
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
        self.append(event)
        return event

    def latest(self, n: int = 10) -> Tuple[GuardianEvent, ...]:
        """n event terbaru."""
        return tuple(self._events[-n:])

    def by_severity(self, severity: str) -> Tuple[GuardianEvent, ...]:
        """Filter by severity."""
        return tuple(e for e in self._events if e.severity == severity)

    def by_category(self, category: str) -> Tuple[GuardianEvent, ...]:
        """Filter by category."""
        return tuple(e for e in self._events if e.category == category)

    def by_policy(self) -> Tuple[GuardianEvent, ...]:
        """Filter: policy events."""
        return tuple(e for e in self._events if e.category == "policy")

    def by_health(self) -> Tuple[GuardianEvent, ...]:
        """Filter: health events."""
        return tuple(e for e in self._events if e.category == "health")

    def by_watchdog(self) -> Tuple[GuardianEvent, ...]:
        """Filter: watchdog events."""
        return tuple(e for e in self._events if e.category == "watchdog")

    def clear(self) -> None:
        self._events.clear()

    def to_timeline(self, source: str = "guardian") -> GuardianTimeline:
        return GuardianTimeline(events=tuple(self._events), source=source)
