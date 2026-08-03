"""RuntimeHealth — aggregate health over the seven Runtime Units (E1-001).

RuntimeHealth queries each composed unit's health source and produces one
aggregate status. The aggregate follows a deterministic rule over the seven
units:

    * all units Healthy                    -> Healthy
    * any unit Failed or missing           -> Failed
    * otherwise (at least one Degraded)    -> Degraded

Unit health reports are heterogeneous (string status or dict with
status/lifecycle/health keys). The composition layer normalises them and never
forces a value a unit did not report.

Authority: E1-001 | I0-001 R9 (health exposed)
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional, Tuple

from .exceptions import RuntimeCompositionError
from .interfaces import HealthProvider


class HealthStatus(str, Enum):
    """Aggregate health status for the composed runtime (E1-001)."""

    HEALTHY = "Healthy"
    DEGRADED = "Degraded"
    FAILED = "Failed"


#: Per-unit health normalisation. A health report may be a string
#: (e.g. HealthStatus, "available", "unavailable") or a dict with a
#: status/state/health key. We resolve to a known enum.
def _normalise(value) -> HealthStatus:
    if isinstance(value, dict):
        for key in ("status", "state", "health", "lifecycle"):
            if key in value and value[key] is not None:
                value = value[key]
                break
    s = str(value).upper()
    if "FAIL" in s or "UNAVAILABLE" in s or "DOWN" in s:
        return HealthStatus.FAILED
    if "DEGRAD" in s:
        return HealthStatus.DEGRADED
    if "HEALTHY" in s or "AVAILABLE" in s or "READY" in s or "UP" in s:
        return HealthStatus.HEALTHY
    # Unknown/unrecognised -> treat as failed (not a known status).
    return HealthStatus.FAILED


class RuntimeHealth:
    """Aggregate health over all composed runtime units.

    Attributes:
        providers: unit identity -> HealthProvider (health callable).
    """

    def __init__(
        self,
        providers: Optional[Dict[str, HealthProvider]] = None,
    ) -> None:
        self._providers: Dict[str, HealthProvider] = dict(providers or {})

    def register(self, provider: HealthProvider) -> None:
        """Register a health provider for a unit.

        Args:
            provider: a HealthProvider wrapping a unit's get_health callable.
        """
        self._providers[provider.unit_id] = provider

    def provider_ids(self) -> List[str]:
        """All registered provider ids (stable order)."""
        return sorted(self._providers.keys())

    def unit_health(self, unit_id: str) -> HealthStatus:
        """Health for a single unit.

        Raises:
            RuntimeCompositionError: if no provider is registered.
        """
        if unit_id not in self._providers:
            raise RuntimeCompositionError(
                "No health provider registered for unit: %s" % unit_id
            )
        return _normalise(self._providers[unit_id]())

    def all_health(self) -> Dict[str, HealthStatus]:
        """Health for all units, keyed by unit identity (stable order)."""
        return {
            uid: self.unit_health(uid)
            for uid in sorted(self._providers)
        }

    def aggregate(self) -> HealthStatus:
        """Aggregate health across all units (deterministic rule)."""
        statuses = list(self.all_health().values())
        if not statuses:
            return HealthStatus.FAILED
        if any(s == HealthStatus.FAILED for s in statuses):
            return HealthStatus.FAILED
        if all(s == HealthStatus.HEALTHY for s in statuses):
            return HealthStatus.HEALTHY
        return HealthStatus.DEGRADED

    def is_healthy(self) -> bool:
        """True iff aggregate health is Healthy."""
        return self.aggregate() == HealthStatus.HEALTHY

    def is_failed(self) -> bool:
        """True iff aggregate health is Failed."""
        return self.aggregate() == HealthStatus.FAILED

    def summary(self) -> Tuple[HealthStatus, Dict[str, HealthStatus]]:
        """Return (aggregate, per-unit map) in one call."""
        return self.aggregate(), self.all_health()
