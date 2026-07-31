# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 141 - Mission Monitoring: mission_statistics.

Statistics for a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class MissionStatistics:
    """Immutable statistics snapshot for a mission."""

    mission_id: str
    progress: float = 0.0
    preview_only: bool = True
    extra: Dict[str, float] = field(default_factory=dict)
