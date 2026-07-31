# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 131 - Monitoring: orchestration_statistics.

Statistics derived from orchestration metrics. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class OrchestrationStatistics:
    """Immutable statistics snapshot."""

    plans: int = 0
    runtimes: int = 0
    preview_only: bool = True
    extra: Dict[str, float] = field(default_factory=dict)
