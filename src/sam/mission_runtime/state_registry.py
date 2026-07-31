# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 139 - Mission State: state_registry.

Registry of mission states. Pure in-memory, sync.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from .mission_state import MissionState


@dataclass(frozen=True)
class StateRegistrationResult:
    mission_id: str
    accepted: bool
    reason: str = ""


class StateRegistry:
    """Holds the latest state per mission."""

    def __init__(self) -> None:
        self._states: Dict[str, MissionState] = {}

    def set(self, state: MissionState) -> StateRegistrationResult:
        self._states[state.mission_id] = state
        return StateRegistrationResult(
            mission_id=state.mission_id, accepted=True, reason="set"
        )

    def get(self, mission_id: str) -> Optional[MissionState]:
        return self._states.get(mission_id)

    def all(self) -> Tuple[MissionState, ...]:
        return tuple(sorted(self._states.values(), key=lambda s: s.mission_id))

    def count(self) -> int:
        return len(self._states)
