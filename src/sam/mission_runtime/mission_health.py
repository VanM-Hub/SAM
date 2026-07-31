# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 141 - Mission Monitoring: mission_health.

Health of a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class MissionHealth:
    """Immutable health status for a mission."""

    mission_id: str
    state: str = "healthy"  # healthy | degraded | critical
    checks: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_healthy(self) -> bool:
        return self.state == "healthy"

    @property
    def is_critical(self) -> bool:
        return self.state == "critical"
