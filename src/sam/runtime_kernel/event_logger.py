"""Event Logger — pencatat event."""
from __future__ import annotations
from typing import Dict, List
from sam.runtime_kernel.runtime_event import RuntimeEvent


class EventLogger:
    """Logger event — preview-only."""

    def __init__(self) -> None:
        self._log: Dict[str, RuntimeEvent] = {}

    def log(self, event: RuntimeEvent) -> None:
        self._log[event.event_id] = event

    def get(self, event_id: str) -> RuntimeEvent | None:
        return self._log.get(event_id)

    def find_by_source(self, source: str) -> List[RuntimeEvent]:
        return [e for e in self._log.values() if e.source == source]

    def count(self) -> int:
        return len(self._log)

    def list_all(self) -> List[RuntimeEvent]:
        return list(self._log.values())
