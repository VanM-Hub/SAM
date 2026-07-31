# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 134 - Mission Foundation: mission_builder.

Opens a mission descriptor from a request using the registry.
Manages the mission lifecycle; never executes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .mission_request import MissionRequest
from .mission_registry import MissionRegistry
from .mission_descriptor import MissionDescriptor


@dataclass(frozen=True)
class MissionOpenPlan:
    """Immutable plan produced when opening a mission."""

    mission_id: str
    chain: Tuple[str, ...] = field(default_factory=tuple)
    opened: bool = True

    @property
    def is_plan_only(self) -> bool:
        return True


class MissionBuilder:
    """Opens missions and arranges their lifecycle (planning only)."""

    def __init__(self, registry: MissionRegistry) -> None:
        self._registry = registry

    def open(self, request: MissionRequest) -> Optional[MissionOpenPlan]:
        """Open a mission by registering its descriptor."""
        if not request.mission_id:
            return None
        descriptor = MissionDescriptor(
            mission_id=request.mission_id,
            name=request.mission_id,
        )
        self._registry.register(descriptor)
        return MissionOpenPlan(
            mission_id=request.mission_id,
            chain=(request.mission_id,),
            opened=True,
        )
