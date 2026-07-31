# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 131 - Monitoring: orchestration_metrics.

Metrics for orchestration. Pure DTO, immutable (planning only).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class OrchestrationMetrics:
    """Immutable snapshot of orchestration counters."""

    requests_counted: int = 0
    plans_built: int = 0
    external_calls: int = 0  # always 0 (planning only)
    dimensions: Dict[str, int] = field(default_factory=dict)

    @property
    def is_preview(self) -> bool:
        """Orchestration never makes external calls."""
        return self.external_calls == 0
