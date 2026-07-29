"""
Guardian Live Event DTO.

Immutable event types for the Guardian Live Runtime.
All DTOs are frozen dataclasses. No async, no threading, no network.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Dict, List, Optional
from datetime import datetime
import uuid


class GuardianEventType(Enum):
    """Types of events flowing through the Guardian Live Runtime."""

    OBSERVATION_UPDATE = auto()
    GUARDIAN_HEALTH_UPDATE = auto()
    DASHBOARD_REFRESH = auto()
    REASONING_TRIGGER = auto()
    LEARNING_UPDATE = auto()
    EXECUTION_PREVIEW = auto()
    CONVERSATION_UPDATE = auto()
    ALERT_RAISED = auto()
    ALERT_CLEARED = auto()
    STATE_CHANGE = auto()
    CONFIG_CHANGE = auto()
    SYSTEM_STATUS = auto()


class GuardianEventPriority(Enum):
    """Priority levels for event dispatch ordering."""

    CRITICAL = 0
    HIGH = 1
    MEDIUM = 2
    LOW = 3
    BACKGROUND = 4


class GuardianEventSource(Enum):
    """Source components that can emit events."""

    OBSERVATION = auto()
    GUARDIAN = auto()
    REASONING = auto()
    DECISION = auto()
    LEARNING = auto()
    EXECUTION = auto()
    DASHBOARD = auto()
    CONVERSATION = auto()
    PLUGIN = auto()
    CONNECTOR = auto()
    PROVIDER = auto()
    INTEGRATION = auto()
    SYSTEM = auto()
    MISSION = auto()
    APPROVAL = auto()
    FILESYSTEM = auto()
    GIT = auto()


@dataclass(frozen=True)
class GuardianEventMetadata:
    """Immutable metadata attached to every event."""

    event_type: GuardianEventType
    priority: GuardianEventPriority
    source: GuardianEventSource
    timestamp: float
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "event_type": self.event_type.name,
            "priority": self.priority.name,
            "priority_order": self.priority.value,
            "source": self.source.name,
            "timestamp": self.timestamp,
            "version": self.version,
        }


@dataclass(frozen=True)
class GuardianEvent:
    """
    Immutable event for the Guardian Live Runtime.

    Core unit of communication. Once created, it cannot be modified.
    """

    metadata: GuardianEventMetadata = field(compare=False)
    payload: Any = field(compare=False)
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = field(default=None, compare=False)
    parent_event_id: Optional[str] = field(default=None, compare=False)

    def to_dict(self) -> Dict[str, Any]:
        result: Dict[str, Any] = {
            "event_id": self.event_id,
            "metadata": self.metadata.to_dict(),
            "payload": self._serialize_payload(),
        }
        if self.correlation_id:
            result["correlation_id"] = self.correlation_id
        if self.parent_event_id:
            result["parent_event_id"] = self.parent_event_id
        return result

    def _serialize_payload(self) -> Any:
        """Serialize payload to a dict-friendly form."""
        if hasattr(self.payload, "to_dict"):
            return self.payload.to_dict()
        if isinstance(self.payload, (dict, list, str, int, float, bool)):
            return self.payload
        if self.payload is None:
            return None
        return str(self.payload)

    def with_parent(self, parent_event_id: str) -> "GuardianEvent":
        """Create a new event linked to a parent (immutable pattern)."""
        return GuardianEvent(
            metadata=self.metadata,
            payload=self.payload,
            event_id=self.event_id,
            correlation_id=self.correlation_id,
            parent_event_id=parent_event_id,
        )


@dataclass(frozen=True)
class GuardianEventSnapshot:
    """
    Immutable point-in-time snapshot of the current event state.

    Captures all events that have passed through the dispatcher
    in a single dispatch cycle.
    """

    cycle_id: str
    timestamp: float
    total_events: int
    events: List[GuardianEvent]
    priority_counts: Dict[str, int]
    source_counts: Dict[str, int]
    completed: bool
    errors: List[str] = field(default_factory=list)
    duration_ms: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cycle_id": self.cycle_id,
            "timestamp": self.timestamp,
            "total_events": self.total_events,
            "events": [e.to_dict() for e in self.events],
            "priority_counts": dict(self.priority_counts),
            "source_counts": dict(self.source_counts),
            "completed": self.completed,
            "errors": list(self.errors),
            "duration_ms": self.duration_ms,
        }
