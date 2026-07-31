# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 134 - Mission Foundation: conversation_mission.

Read-only conversation bridge for mission foundation.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from .mission_registry import MissionRegistry
from .mission_builder import MissionBuilder, MissionOpenPlan
from .mission_request import MissionRequest
from .mission_descriptor import MissionDescriptor


class ConversationMissionBridge:
    """Read-only bridge exposing mission foundation."""

    def __init__(self, registry: MissionRegistry) -> None:
        self._registry = registry
        self._builder = MissionBuilder(registry)

    def count(self) -> int:
        return self._registry.count()

    def locate(self, mission_id: str) -> Optional[MissionDescriptor]:
        return self._registry.get(mission_id)

    def open(self, request: MissionRequest) -> MissionOpenPlan:
        return self._builder.open(request)

    def list_names(self) -> Tuple[str, ...]:
        return tuple(m.name for m in self._registry.all())

    def summary(self) -> Dict[str, int]:
        return {"missions": self._registry.count()}
