# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 140 - Mission Coordination: coordination_summary.

Summarizes coordination. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class CoordinationSummary:
    """Immutable summary of coordination."""

    mission_id: str
    runtimes: Tuple[str, ...]
    total: int = 0
