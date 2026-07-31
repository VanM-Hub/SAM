# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 128 - Scheduling: schedule_request.

Request to schedule runtimes. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class ScheduleRequest:
    """Immutable request describing what to schedule."""

    schedule_id: str
    runtimes: Tuple[str, ...] = field(default_factory=tuple)
    priority: int = 0
    metadata: Dict[str, str] = field(default_factory=dict)
