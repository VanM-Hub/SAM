"""Connector Health - WP-17 (MISSION-5.2 / IP-5.2-002).

Health model untuk connector. Observasional, read-only.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple


class ConnectorHealthState(str, Enum):
    """Kelas status kesehatan connector."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ConnectorHealth:
    """Status kesehatan connector."""

    connector_id: str
    state: ConnectorHealthState = ConnectorHealthState.UNKNOWN
    latency_ms: Optional[float] = None
    notes: Tuple[str, ...] = field(default_factory=tuple)
    observed_at: str = field(default_factory=_now_utc)

    @property
    def healthy(self) -> bool:
        return self.state == ConnectorHealthState.HEALTHY

    def as_dict(self) -> dict:
        return {
            "connector_id": self.connector_id,
            "state": self.state.value,
            "healthy": self.healthy,
            "latency_ms": self.latency_ms,
            "notes": list(self.notes),
            "observed_at": self.observed_at,
        }


class ConnectorHealthCheck:
    """Assessment kesehatan connector (observasional)."""

    def assess(
        self,
        connector_id: str,
        *,
        reachable: bool = True,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> ConnectorHealth:
        if error:
            state = ConnectorHealthState.UNHEALTHY
        elif not reachable:
            state = ConnectorHealthState.DEGRADED
        elif latency_ms is not None and latency_ms > 5000:
            state = ConnectorHealthState.DEGRADED
        else:
            state = ConnectorHealthState.HEALTHY
        notes = (error,) if error else ()
        return ConnectorHealth(connector_id=connector_id, state=state, latency_ms=latency_ms, notes=notes)
