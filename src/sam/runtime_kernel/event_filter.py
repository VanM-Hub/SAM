"""Event Filter — filter event."""
from __future__ import annotations
from typing import List
from sam.runtime_kernel.runtime_event import RuntimeEvent


class EventFilter:
    """Filter event — preview-only."""

    def filter_by_type(self, events: List[RuntimeEvent], event_type: str) -> List[RuntimeEvent]:
        return [e for e in events if e.event_type == event_type]

    def filter_by_source(self, events: List[RuntimeEvent], source: str) -> List[RuntimeEvent]:
        return [e for e in events if e.source == source]

    def filter_recent(self, events: List[RuntimeEvent], limit: int) -> List[RuntimeEvent]:
        return events[-limit:] if limit < len(events) else events
