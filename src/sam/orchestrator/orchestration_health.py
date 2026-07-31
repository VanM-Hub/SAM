# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 131 - Monitoring: orchestration_health.

Health status of orchestration. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class OrchestrationHealth:
    """Immutable health status for orchestration."""

    state: str = "healthy"  # healthy | degraded | unknown
    checks: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_healthy(self) -> bool:
        return self.state == "healthy"

    @property
    def is_degraded(self) -> bool:
        return self.state == "degraded"
