# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 142 - Mission Runtime: mission_status.

Status of the mission runtime. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MissionStatus:
    """Immutable status of the mission runtime."""

    state: str = "ready"

    @property
    def is_ready(self) -> bool:
        return self.state == "ready"
