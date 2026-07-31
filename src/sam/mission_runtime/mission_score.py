# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 143 - Mission Certification: mission_score.

Score for the mission runtime. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MissionScore:
    """Immutable score of mission runtime quality."""

    score: float = 100.0
    certified: bool = True

    @property
    def passed(self) -> bool:
        return self.certified and self.score >= 90.0
