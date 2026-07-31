# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 141 - Mission Monitoring: mission_metrics.

Metrics for a mission. Pure DTO, immutable (planning only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class MissionMetrics:
    """Immutable metrics per mission."""

    mission_id: str
    objectives_total: int = 0
    checkpoints_reached: int = 0
    external_calls: int = 0  # always 0 (planning only)
    dimensions: Dict[str, int] = field(default_factory=dict)

    @property
    def is_preview(self) -> bool:
        return self.external_calls == 0
