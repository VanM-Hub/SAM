# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 141 - Mission Monitoring: mission_history.

History of mission health events. Append-only, sync.
"""
from __future__ import annotations

from typing import List, Tuple

from .mission_health import MissionHealth


class MissionHistory:
    """Append-only history of mission health events."""

    def __init__(self) -> None:
        self._events: List[MissionHealth] = []

    def record(self, health: MissionHealth) -> None:
        self._events.append(health)

    def events(self) -> Tuple[MissionHealth, ...]:
        return tuple(self._events)

    def count(self) -> int:
        return len(self._events)

    def clear(self) -> None:
        self._events.clear()
