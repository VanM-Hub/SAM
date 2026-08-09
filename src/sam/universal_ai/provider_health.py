"""AI Provider Health - WP-07 (MISSION-5.1 / IP-5.1-001).

Health model untuk AI Provider dan AI Model. Observasional, read-only;
tidak melakukan automatic failover atau recovery.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple


class HealthState(str, Enum):
    """Kelas status kesehatan."""

    UNKNOWN = "unknown"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    NOT_READY = "not_ready"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class HealthEvidence:
    """Bukti observasi kesehatan."""

    observed_at: str
    state: HealthState
    note: str = ""
    latency_ms: Optional[float] = None

    def as_dict(self) -> dict:
        return {
            "observed_at": self.observed_at,
            "state": self.state.value,
            "note": self.note,
            "latency_ms": self.latency_ms,
        }


@dataclass(frozen=True)
class ProviderHealth:
    """Status kesehatan provider + model-nya (read-only snapshot)."""

    provider_id: str
    state: HealthState = HealthState.UNKNOWN
    latency_ms: Optional[float] = None
    notes: Tuple[str, ...] = field(default_factory=tuple)
    evidence: Optional[HealthEvidence] = None

    @property
    def healthy(self) -> bool:
        return self.state == HealthState.READY

    @property
    def failure_state(self) -> bool:
        return self.state == HealthState.FAILED

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "state": self.state.value,
            "healthy": self.healthy,
            "latency_ms": self.latency_ms,
            "notes": list(self.notes),
            "evidence": self.evidence.as_dict() if self.evidence else None,
        }


class AIProviderHealthCheck:
    """Melakukan assessment kesehatan (observasional, non-execution)."""

    def assess(
        self,
        provider_id: str,
        *,
        reachable: bool = True,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> ProviderHealth:
        if error:
            state = HealthState.FAILED
        elif not reachable:
            state = HealthState.NOT_READY
        elif latency_ms is not None and latency_ms > 5000:
            state = HealthState.DEGRADED
        else:
            state = HealthState.READY
        notes = (error,) if error else ()
        return ProviderHealth(
            provider_id=provider_id,
            state=state,
            latency_ms=latency_ms,
            notes=notes,
            evidence=HealthEvidence(
                observed_at=_now_utc(), state=state, note=error or "", latency_ms=latency_ms
            ),
        )
