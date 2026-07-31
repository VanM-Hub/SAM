# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 142 - Mission Runtime: mission_pipeline.

The mission-oriented pipeline. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class MissionPipeline:
    """Immutable description of the mission pipeline stages."""

    pipeline_id: str = "mission"
    stages: Tuple[str, ...] = field(
        default_factory=lambda: (
            "Foundation",
            "Definition",
            "Objectives",
            "Resources",
            "Timeline",
            "State",
            "Coordination",
            "Monitoring",
            "Runtime",
            "Certification",
        )
    )

    @property
    def stage_count(self) -> int:
        return len(self.stages)
