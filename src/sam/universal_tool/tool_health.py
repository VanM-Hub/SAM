"""Tool Health - WP-07 (MISSION-5.2 / IP-5.2-001).

Health model untuk Tool. Observasional, read-only; tidak automatic recovery.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional, Tuple


class ToolHealthState(str, Enum):
    """Kelas status kesehatan tool."""

    UNKNOWN = "unknown"
    READY = "ready"
    DEGRADED = "degraded"
    FAILED = "failed"
    NOT_READY = "not_ready"


def _now_utc() -> str:
    return datetime.utcnow().isoformat() + "Z"


@dataclass(frozen=True)
class ToolHealth:
    """Status kesehatan tool (read-only snapshot)."""

    tool_id: str
    state: ToolHealthState = ToolHealthState.UNKNOWN
    latency_ms: Optional[float] = None
    notes: Tuple[str, ...] = field(default_factory=tuple)
    observed_at: str = field(default_factory=_now_utc)

    @property
    def healthy(self) -> bool:
        return self.state == ToolHealthState.READY

    def as_dict(self) -> dict:
        return {
            "tool_id": self.tool_id,
            "state": self.state.value,
            "healthy": self.healthy,
            "latency_ms": self.latency_ms,
            "notes": list(self.notes),
            "observed_at": self.observed_at,
        }


class ToolHealthCheck:
    """Melakukan assessment kesehatan tool (observasional)."""

    def assess(
        self,
        tool_id: str,
        *,
        reachable: bool = True,
        latency_ms: Optional[float] = None,
        error: Optional[str] = None,
    ) -> ToolHealth:
        if error:
            state = ToolHealthState.FAILED
        elif not reachable:
            state = ToolHealthState.NOT_READY
        elif latency_ms is not None and latency_ms > 5000:
            state = ToolHealthState.DEGRADED
        else:
            state = ToolHealthState.READY
        notes = (error,) if error else ()
        return ToolHealth(tool_id=tool_id, state=state, latency_ms=latency_ms, notes=notes)
