"""Investigation Timeline - WP-06 (MISSION-4.2 / IP-4.2-001).

Menyusun kronologi investigasi secara deterministik. Seluruh aktivitas
memiliki timestamp, urutan konsisten, timeline immutable, dapat dijelaskan.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class TimelineEvent:
    """Satu event dalam timeline (immutable)."""

    sequence: int
    timestamp: str
    event_type: str  # created | scope | evidence | observation | analysis | completed
    detail: str = ""
    entity_id: str = ""

    def as_dict(self) -> dict:
        return {
            "sequence": self.sequence,
            "timestamp": self.timestamp,
            "event_type": self.event_type,
            "detail": self.detail,
            "entity_id": self.entity_id,
        }


@dataclass(frozen=True)
class TimelineMetadata:
    """Metadata timeline."""

    investigation_id: str
    started_at: str
    builder: str = "investigation_timeline"

    def as_dict(self) -> dict:
        return {
            "investigation_id": self.investigation_id,
            "started_at": self.started_at,
            "builder": self.builder,
        }


@dataclass(frozen=True)
class InvestigationTimeline:
    """Kronologi investigasi (immutable, urutan deterministik)."""

    metadata: TimelineMetadata
    events: Tuple[TimelineEvent, ...] = field(default_factory=tuple)
    timeline_hash: str = ""

    @property
    def event_count(self) -> int:
        return len(self.events)

    def as_dict(self) -> dict:
        return {
            "metadata": self.metadata.as_dict(),
            "event_count": self.event_count,
            "events": [e.as_dict() for e in self.events],
            "timeline_hash": self.timeline_hash,
        }


class TimelineOrdering:
    """Urutan chronologis deterministik (sequence bertambah + timestamp)."""

    @staticmethod
    def key(event: TimelineEvent) -> Tuple[int, str]:
        return (event.sequence, event.timestamp)


class TimelineBuilder:
    """Membangun timeline secara increment (immutable append)."""

    def __init__(self, investigation_id: str) -> None:
        self._metadata = TimelineMetadata(
            investigation_id=investigation_id,
            started_at=_now_utc(),
        )
        self._events: List[TimelineEvent] = []
        self._counter = 0

    @property
    def investigation_id(self) -> str:
        return self._metadata.investigation_id

    def record(
        self,
        event_type: str,
        detail: str = "",
        entity_id: str = "",
        timestamp: Optional[str] = None,
    ) -> "TimelineBuilder":
        self._counter += 1
        event = TimelineEvent(
            sequence=self._counter,
            timestamp=timestamp or _now_utc(),
            event_type=event_type,
            detail=detail,
            entity_id=entity_id,
        )
        self._events.append(event)
        return self

    def build(self) -> InvestigationTimeline:
        ordered = tuple(sorted(self._events, key=TimelineOrdering.key))
        return InvestigationTimeline(
            metadata=self._metadata,
            events=ordered,
            timeline_hash=self._hash(ordered),
        )

    @staticmethod
    def _hash(events: Tuple[TimelineEvent, ...]) -> str:
        import hashlib

        h = hashlib.sha256()
        for e in events:
            h.update(f"{e.sequence}:{e.timestamp}:{e.event_type}".encode("utf-8"))
        return h.hexdigest()


class TimelineViewer:
    """Interface read-only untuk melihat timeline."""

    @staticmethod
    def view(timeline: InvestigationTimeline) -> Dict[str, Any]:
        return timeline.as_dict()

    @staticmethod
    def by_type(
        timeline: InvestigationTimeline, event_type: str
    ) -> Tuple[TimelineEvent, ...]:
        return tuple(
            e for e in timeline.events if e.event_type == event_type
        )

    @staticmethod
    def range(
        timeline: InvestigationTimeline,
        start_sequence: int,
        end_sequence: Optional[int] = None,
    ) -> Tuple[TimelineEvent, ...]:
        end = end_sequence if end_sequence is not None else float("inf")
        return tuple(
            e
            for e in timeline.events
            if start_sequence <= e.sequence <= end
        )
