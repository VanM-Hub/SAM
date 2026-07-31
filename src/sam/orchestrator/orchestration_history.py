# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 131 - Monitoring: orchestration_history.

History of orchestration events. Sync, in-memory.
"""
from __future__ import annotations

from typing import List, Tuple

from .orchestration_health import OrchestrationHealth


class OrchestrationHistory:
    """Append-only history of orchestration health events."""

    def __init__(self) -> None:
        self._events: List[OrchestrationHealth] = []

    def record(self, health: OrchestrationHealth) -> None:
        self._events.append(health)

    def events(self) -> Tuple[OrchestrationHealth, ...]:
        return tuple(self._events)

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
