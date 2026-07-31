# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 128 - Scheduling: schedule_summary.

Summarizes a schedule plan. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class ScheduleSummary:
    """Immutable summary of a schedule."""

    schedule_id: str
    order: Tuple[str, ...]
    total_stages: int = 0
