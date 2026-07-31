# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 142 - Mission Runtime: mission_reporter.

Report of the mission runtime. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass

from .mission_status import MissionStatus
from .mission_snapshot import MissionSnapshot


@dataclass(frozen=True)
class MissionReporter:
    """Immutable report of mission runtime readiness."""

    status: MissionStatus
    snapshot: MissionSnapshot
    runtime_ready: bool = True

    @property
    def ok(self) -> bool:
        return self.runtime_ready and self.status.is_ready and self.snapshot.ready
