# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 138 - Mission Timeline: timeline_checkpoint.

A checkpoint in a mission timeline. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TimelineCheckpoint:
    """Immutable checkpoint within a mission timeline."""

    checkpoint_id: str
    order: int = 0
    label: str = ""
