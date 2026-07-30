"""Activation Monitor — pemantau siklus aktivasi."""
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from sam.activation.activation_package import ActivationPackage


@dataclass(frozen=True)
class MonitorEvent:
    event_id: str = ""
    event_type: str = ""
    package_ref: str = ""
    timestamp: float = 0.0
    details: Dict[str, Any] = field(default_factory=dict)


class ActivationMonitor:
    """Monitor aktivasi — mencatat event dalam siklus."""

    def __init__(self):
        self._events: List[MonitorEvent] = []

    def record(self, event_type: str, package: ActivationPackage,
               timestamp: float = 0.0) -> MonitorEvent:
        event = MonitorEvent(
            event_id=f"evt_{len(self._events) + 1}",
            event_type=event_type,
            package_ref=package.package_id,
            timestamp=timestamp,
            details={"confidence": package.confidence, "candidates": package.total_candidates},
        )
        self._events.append(event)
        return event

    def list_events(self, limit: int = 10) -> List[MonitorEvent]:
        return self._events[-limit:]

    def count_events(self) -> int:
        return len(self._events)

    def by_type(self, event_type: str) -> List[MonitorEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def clear(self) -> None:
        self._events.clear()
