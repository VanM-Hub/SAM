# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 142 - Mission Runtime: mission_snapshot.

Snapshot of the mission runtime. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass

from .mission_status import MissionStatus
from .mission_pipeline import MissionPipeline


@dataclass(frozen=True)
class MissionSnapshot:
    """Immutable snapshot of the mission runtime."""

    status: MissionStatus
    pipeline: MissionPipeline
    runtime_version: str = "1.0.0"

    @property
    def ready(self) -> bool:
        return self.status.is_ready
