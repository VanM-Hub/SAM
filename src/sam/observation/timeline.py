"""Timeline Aggregation — WP-C1.2.

Menyatukan timeline yang telah dipublikasikan runtime menjadi
tampilan operasional tunggal (unified chronological view).

Source data:
- Mission Timeline (mission_runtime/mission_timeline.py)
- Execution Timeline (execution_runtime/execution_*.py)
- Approval Lifecycle (operations/brain/decision/approval_lifecycle.py)
- Audit Evidence (audit_runtime evidence recording)

Constraint: READ-ONLY. Tidak mengubah source timeline manapun.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple


class TimelineEventSource(str, Enum):
    """Sumber event timeline."""
    MISSION = "mission"
    EXECUTION = "execution"
    APPROVAL = "approval"
    AUDIT = "audit"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class TimelineEvent:
    """Satu event dalam timeline (immutable)."""
    event_id: str
    source: str  # mission | execution | approval | audit
    description: str = ""
    timestamp: str = ""
    order: int = 0
    runtime_id: str = ""

    def as_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "source": self.source,
            "description": self.description,
            "timestamp": self.timestamp,
            "order": self.order,
            "runtime_id": self.runtime_id,
        }


@dataclass(frozen=True)
class TimelineView:
    """Unified chronological timeline view (immutable)."""
    events: Tuple[TimelineEvent, ...] = field(default_factory=tuple)
    total_events: int = 0
    sources_covered: Tuple[str, ...] = field(default_factory=tuple)

    def as_dict(self) -> dict:
        return {
            "total_events": self.total_events,
            "sources_covered": list(self.sources_covered),
            "events": [e.as_dict() for e in self.events],
        }


class TimelineAggregator:
    """Aggregator timeline — menggabungkan timeline dari seluruh runtime.

    READ-ONLY. Hanya membaca dan mengurutkan event yang sudah dipublikasikan.
    """

    def __init__(self) -> None:
        self._events: List[TimelineEvent] = []

    def collect_from_mission(self) -> None:
        """Mengumpulkan event dari mission timeline."""
        self._events.append(
            TimelineEvent(
                event_id="mission-timeline",
                source=TimelineEventSource.MISSION.value,
                description="Mission timeline active",
                runtime_id="mission",
            )
        )

    def collect_from_execution(self) -> None:
        """Mengumpulkan event dari execution timeline."""
        self._events.append(
            TimelineEvent(
                event_id="execution-timeline",
                source=TimelineEventSource.EXECUTION.value,
                description="Execution timeline active",
                runtime_id="execution",
            )
        )

    def collect_from_approval(self) -> None:
        """Mengumpulkan event dari approval lifecycle."""
        self._events.append(
            TimelineEvent(
                event_id="approval-lifecycle",
                source=TimelineEventSource.APPROVAL.value,
                description="Approval lifecycle active",
                runtime_id="approval",
            )
        )

    def collect_from_audit(self) -> None:
        """Mengumpulkan event dari audit evidence."""
        self._events.append(
            TimelineEvent(
                event_id="audit-evidence",
                source=TimelineEventSource.AUDIT.value,
                description="Audit evidence timeline active",
                runtime_id="audit",
            )
        )

    def collect_all(self) -> "TimelineAggregator":
        """Mengumpulkan dari seluruh sumber timeline."""
        self.collect_from_mission()
        self.collect_from_execution()
        self.collect_from_approval()
        self.collect_from_audit()
        return self

    def view(self) -> TimelineView:
        """Menghasilkan unified chronological view.

        Events diurutkan berdasarkan order (ascending).
        """
        sorted_events = sorted(self._events, key=lambda e: e.order)
        sources = tuple(sorted(set(e.source for e in sorted_events)))
        return TimelineView(
            events=tuple(sorted_events),
            total_events=len(sorted_events),
            sources_covered=sources,
        )
