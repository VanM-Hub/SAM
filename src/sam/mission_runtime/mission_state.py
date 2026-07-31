# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 139 - Mission State: mission_state.

State of a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MissionState:
    """Immutable state of a mission."""

    mission_id: str
    state: str = "open"  # open | active | closed
    stage: int = 0

    @property
    def is_open(self) -> bool:
        return self.state == "open"

    @property
    def is_active(self) -> bool:
        return self.state == "active"

    @property
    def is_closed(self) -> bool:
        return self.state == "closed"
