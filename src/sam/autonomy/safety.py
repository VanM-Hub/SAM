"""Safety Envelope — Sprint 32.

Bounded operational boundaries that autonomous actions must not violate.
If an action would cross a boundary, it is blocked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

import structlog

logger = structlog.get_logger()


@dataclass
class SafetyBoundary:
    """A single operational boundary.

    Attributes:
        name: Boundary name (e.g. "max_cpu_usage", "max_cost_per_hour").
        metric: Metric this boundary applies to.
        max_value: Maximum allowed value.
        min_value: Minimum allowed value (optional).
        enabled: Whether this boundary is active.
        severity: "warn", "block" — whether to warn or block.
    """
    name: str = ""
    metric: str = ""
    max_value: float = 100.0
    min_value: float = 0.0
    enabled: bool = True
    severity: str = "block"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "metric": self.metric,
            "max_value": self.max_value,
            "min_value": self.min_value,
            "enabled": self.enabled,
            "severity": self.severity,
        }


class SafetyEnvelope:
    """Manages and checks operational safety boundaries."""

    DEFAULT_BOUNDARIES = [
        SafetyBoundary(name="max_cpu", metric="cpu_usage", max_value=95.0, severity="block"),
        SafetyBoundary(name="max_memory", metric="memory_usage", max_value=95.0, severity="block"),
        SafetyBoundary(name="max_concurrent_actions", metric="concurrent_actions", max_value=10, severity="block"),
        SafetyBoundary(name="min_confidence", metric="operational_confidence", min_value=30.0, max_value=100.0, severity="warn"),
        SafetyBoundary(name="max_cost_per_hour", metric="cost_per_hour", max_value=1000.0, severity="warn"),
    ]

    def __init__(self) -> None:
        self._boundaries: Dict[str, SafetyBoundary] = {
            b.name: b for b in self.DEFAULT_BOUNDARIES
        }
        self.logger = logger.bind(component="SafetyEnvelope")

    async def check(self, action: Dict[str, Any]) -> bool:
        """Check if an action is safe to execute.

        Args:
            action: Dict with 'metric' values to check.

        Returns:
            True if safe, False if any boundary violated.
        """
        for name, boundary in self._boundaries.items():
            if not boundary.enabled:
                continue
            metric_value = action.get(boundary.metric)
            if metric_value is None:
                continue

            if metric_value < boundary.min_value:
                self.logger.warning(
                    "Safety boundary violated (min)",
                    boundary=name,
                    metric=boundary.metric,
                    value=metric_value,
                    min=boundary.min_value,
                )
                return boundary.severity != "block"  # warn = still safe

            if metric_value > boundary.max_value:
                self.logger.warning(
                    "Safety boundary violated (max)",
                    boundary=name,
                    metric=boundary.metric,
                    value=metric_value,
                    max=boundary.max_value,
                )
                return boundary.severity != "block"

        return True

    async def get_boundaries(self) -> Dict[str, SafetyBoundary]:
        return dict(self._boundaries)

    async def update_boundary(self, boundary: SafetyBoundary) -> None:
        """Add or update a safety boundary."""
        self._boundaries[boundary.name] = boundary
        self.logger.debug("Safety boundary updated", name=boundary.name)

    async def remove_boundary(self, name: str) -> None:
        self._boundaries.pop(name, None)

    async def clear(self) -> None:
        self._boundaries.clear()
