# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 138 - Mission Timeline: timeline_summary.

Summarizes a timeline. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class TimelineSummary:
    """Immutable summary of a mission timeline."""

    mission_id: str
    labels: Tuple[str, ...]
    total_checkpoints: int = 0
