"""Runtime Event Bus — DTOs event."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass(frozen=True)
class RuntimeEvent:
    event_id: str
    event_type: str
    source: str = ""
    payload: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class EventSubscription:
    sub_id: str
    event_type: str
    handler: str = ""
    active: bool = True


@dataclass(frozen=True)
class EventLog:
    log_id: str
    events: List[RuntimeEvent] = field(default_factory=list)
    count: int = 0


@dataclass(frozen=True)
class EventDispatch:
    dispatch_id: str
    event_id: str
    handled: bool = False
    handlers: List[str] = field(default_factory=list)
