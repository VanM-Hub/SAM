"""Real Provider Activation - cancellation/timeout (Sprint 260).

Program C - Real Execution Runtime.
Logika cancellation token & timeout enforcement di provider layer.
Synchronous, no asyncio/thread. Timeout diterapkan sebagai penjaga pada
durasi eksekusi (simulasi deterministik saat tanpa kredensial, dan
diteruskan saat implementasi provider nyata dipanggil).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, Optional


@dataclass(frozen=True)
class ActivationReport:
    """Laporan aktivasi provider (immutable)."""
    provider_id: str
    external_calls: int = 0
    timeout_enforced: bool = False
    cancelled: bool = False
    status: str = "ok"

    def as_dict(self) -> dict:
        return {"provider_id": self.provider_id,
                "external_calls": self.external_calls,
                "timeout_enforced": self.timeout_enforced,
                "cancelled": self.cancelled,
                "status": self.status}


class ProviderCancellation:
    """Token pembatalan. Check point synchronous."""

    def __init__(self, token: str = "") -> None:
        self._token = token
        self._cancelled = False

    def cancel(self) -> None:
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled

    @property
    def token(self) -> str:
        return self._token


def enforce_timeout(elapsed_ms: int, timeout_seconds: int) -> bool:
    """True bila elapsed melebihi timeout (enforcement sync)."""
    return elapsed_ms > (timeout_seconds * 1000)
