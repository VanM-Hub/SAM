"""Execution Health (Sprint 256).

Program C - Real Execution Runtime.
Status kesehatan execution runtime (immutable, no network prober aktif).
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExecutionHealth:
    """Kesehatan execution (immutable)."""
    health_id: str
    ok: bool = True
    provider_available: bool = False
    external_calls: int = 0
    status: str = "healthy"  # healthy | degraded | down

    def as_dict(self) -> dict:
        return {
            "health_id": self.health_id,
            "ok": self.ok,
            "provider_available": self.provider_available,
            "external_calls": self.external_calls,
            "status": self.status,
        }
