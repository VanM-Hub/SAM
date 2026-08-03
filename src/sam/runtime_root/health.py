"""Aggregate health aggregation for the Reference Runtime composition (E1-001).

RuntimeHealth queries each composed unit's health source and produces one
aggregate health status. The aggregate follows a deterministic rule:

- all units AVAILABLE                       -> AVAILABLE
- any unit UNAVAILABLE                      -> UNAVAILABLE
- otherwise (at least one DEGRADED)         -> DEGRADED

Authority: E1-001 | I0-001 R9 (health exposed)
"""

from __future__ import annotations

from enum import Enum
from typing import Callable, Dict, List, Optional, Tuple

from .exceptions import CompositionDefinitionError


class HealthStatus(str, Enum):
    """Aggregate health status for the composed runtime."""

    AVAILABLE = "AVAILABLE"
    DEGRADED = "DEGRADED"
    UNAVAILABLE = "UNAVAILABLE"


#: Per-unit health signal. A unit health report may be a string status
#: (e.g. HealthStatus, "available") or a dict with a status/lifecycle key
#: (heterogeneous unit reporters). We normalise to a known enum.
def _normalise(value) -> HealthStatus:
    if isinstance(value, dict):
        for key in ("status", "state", "health"):
            if key in value and value[key] is not None:
                value = value[key]
                break
    s = str(value).upper()
    if "UNAVAILABLE" in s:
        return HealthStatus.UNAVAILABLE
    if "DEGRADED" in s:
        return HealthStatus.DEGRADED
    if "HEALTHY" in s or "AVAILABLE" in s:
        return HealthStatus.AVAILABLE
    # Fallback: treat unknown as AVAILABLE-equivalent if the value resolved.
    return HealthStatus.AVAILABLE


class RuntimeHealth:
    """Aggregate health over all composed runtime units.

    Attributes:
        units: unit identity -> health callable (no-arg, returns status).
    """

    def __init__(
        self,
        units: Optional[Dict[str, Callable[[], object]]] = None,
    ) -> None:
        self._units: Dict[str, Callable[[], object]] = dict(units or {})

    def register(self, unit_id: str, fn: Callable[[], object]) -> None:
        """Register a health producer for a unit."""
        self._units[unit_id] = fn

    def unit_health(self, unit_id: str) -> HealthStatus:
        """Health for a single unit."""
        if unit_id not in self._units:
            raise CompositionDefinitionError(
                "No health producer registered for unit: %s" % unit_id
            )
        return _normalise(self._units[unit_id]())

    def all_health(self) -> Dict[str, HealthStatus]:
        """Health for all units, keyed by unit identity (stable order)."""
        return {
            uid: self.unit_health(uid)
            for uid in sorted(self._units)
        }

    def aggregate(self) -> HealthStatus:
        """Aggregate health across all units (deterministic rule)."""
        statuses = list(self.all_health().values())
        if not statuses:
            return HealthStatus.UNAVAILABLE
        if all(s == HealthStatus.AVAILABLE for s in statuses):
            return HealthStatus.AVAILABLE
        if any(s == HealthStatus.UNAVAILABLE for s in statuses):
            return HealthStatus.UNAVAILABLE
        return HealthStatus.DEGRADED

    def is_available(self) -> bool:
        """True iff aggregate health is AVAILABLE."""
        return self.aggregate() == HealthStatus.AVAILABLE

    def summary(self) -> Tuple[HealthStatus, Dict[str, HealthStatus]]:
        """Return (aggregate, per-unit map) in one call."""
        return self.aggregate(), self.all_health()
