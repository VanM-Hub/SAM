"""Event Dispatcher — dispatcher event."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_event import RuntimeEvent, EventDispatch, EventSubscription


class EventDispatcher:
    """Dispatcher event — preview-only."""

    def dispatch_to(self, event: RuntimeEvent, handlers: List[str]) -> EventDispatch:
        return EventDispatch(
            dispatch_id=f"disp_{event.event_id}",
            event_id=event.event_id,
            handled=len(handlers) > 0,
            handlers=handlers,
        )

    def batch_dispatch(self, events: List[RuntimeEvent], subs: List[EventSubscription]) -> List[EventDispatch]:
        results: List[EventDispatch] = []
        for event in events:
            handlers = [s.handler for s in subs
                       if s.event_type == event.event_type and s.active]
            results.append(self.dispatch_to(event, handlers))
        return results
