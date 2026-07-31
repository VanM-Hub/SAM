# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 134 - Mission Foundation: mission_registry.

Registry of mission descriptors. Pure in-memory, sync.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Tuple, FrozenSet

from .mission_descriptor import MissionDescriptor


@dataclass(frozen=True)
class MissionRegistrationResult:
    mission_id: str
    accepted: bool
    reason: str = ""


class MissionRegistry:
    """Catalog of mission descriptors."""

    def __init__(self) -> None:
        self._missions: Dict[str, MissionDescriptor] = {}

    def register(self, descriptor: MissionDescriptor) -> MissionRegistrationResult:
        self._missions[descriptor.mission_id] = descriptor
        return MissionRegistrationResult(
            mission_id=descriptor.mission_id, accepted=True, reason="registered"
        )

    def get(self, mission_id: str) -> Optional[MissionDescriptor]:
        return self._missions.get(mission_id)

    def all(self) -> Tuple[MissionDescriptor, ...]:
        return tuple(sorted(self._missions.values(), key=lambda m: m.mission_id))

    def ids(self) -> FrozenSet[str]:
        return frozenset(self._missions.keys())

    def count(self) -> int:
        return len(self._missions)

    def clear(self) -> None:
        self._missions.clear()
