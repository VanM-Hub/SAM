# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 136 - Mission Objectives: objective_summary.

Summarizes objectives. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ObjectiveSummary:
    """Immutable summary of objectives."""

    mission_id: str
    objective_ids: Tuple[str, ...]
    total: int = 0
