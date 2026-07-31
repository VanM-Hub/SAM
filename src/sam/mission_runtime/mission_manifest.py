# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 143 - Mission Certification: mission_manifest.

Manifest of the 11 mission subsystems. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class MissionManifest:
    """Immutable manifest of the mission runtime."""

    version: str = "13.0.0"
    subsystems: Tuple[str, ...] = field(
        default_factory=lambda: (
            "Mission Foundation",
            "Mission Definition",
            "Mission Objectives",
            "Mission Resources",
            "Mission Timeline",
            "Mission State",
            "Mission Coordination",
            "Mission Monitoring",
            "Mission Runtime",
            "Mission Certification",
        )
    )

    @property
    def subsystem_count(self) -> int:
        return len(self.subsystems)
