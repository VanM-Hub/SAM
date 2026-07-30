"""Event Bus — bus event ringan."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_event import RuntimeEvent, EventSubscription, EventDispatch


class EventBus:
    """Bus event — preview-only."""

    def __init__(self) -> None:
        self._subs: Dict[str, EventSubscription] = {}
        self._logs: List[RuntimeEvent] = []

    def subscribe(self, sub: EventSubscription) -> None:
        self._subs[sub.sub_id] = sub

    def unsubscribe(self, sub_id: str) -> bool:
        if sub_id in self._subs:
            del self._subs[sub_id]
            return True
        return False

    def publish(self, event: RuntimeEvent) -> EventDispatch:
        self._logs.append(event)
        handlers: List[str] = []
        for s in self._subs.values():
            if s.event_type == event.event_type and s.active:
                handlers.append(s.handler)
        return EventDispatch(
            dispatch_id=f"d_{event.event_id}",
            event_id=event.event_id,
            handled=len(handlers) > 0,
            handlers=handlers,
        )

    def get_subscription(self, sub_id: str) -> EventSubscription | None:
        return self._subs.get(sub_id)

    def count_subs(self) -> int:
        return len(self._subs)

    def count_events(self) -> int:
        return len(self._logs)

    def find_by_type(self, event_type: str) -> List[RuntimeEvent]:
        return [e for e in self._logs if e.event_type == event_type]
