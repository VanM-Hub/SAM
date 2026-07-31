"""Transition History — riwayat transisi (Sprint 158).

Agent Runtime — riwayat append + read-only query. Deterministik.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class TransitionEvent:
    """Satu peristiwa transisi (immutable)."""
    mission_id: str
    from_state: str
    to_state: str
    allowed: bool = True
    reason: str = ""


class TransitionHistory:
    """Riwayat transisi. Append + read-only query."""

    def __init__(self) -> None:
        self._events: List[TransitionEvent] = []

    def record(self, event: TransitionEvent) -> None:
        self._events.append(event)

    def events(self, mission_id: str = None) -> List[TransitionEvent]:
        if mission_id is None:
            return list(self._events)
        return [e for e in self._events if e.mission_id == mission_id]

    def count(self) -> int:
        return len(self._events)

    def applied_count(self) -> int:
        return sum(1 for e in self._events if e.allowed)
