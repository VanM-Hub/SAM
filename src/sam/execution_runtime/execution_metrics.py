"""Execution Metrics (Sprint 256).

Program C - Real Execution Runtime.
Metrik immutable eksekusi (durasi, retry, calls). Read-only, no network.
"""
from __future__ import annotations
from dataclasses import dataclass, field


@dataclass(frozen=True)
class ExecutionMetrics:
    """Metrik eksekusi (immutable)."""
    metrics_id: str
    execution_id: str
    duration_ms: int = 0
    retries: int = 0
    external_calls: int = 0
    size_payload: int = 0

    def as_dict(self) -> dict:
        return {
            "metrics_id": self.metrics_id,
            "execution_id": self.execution_id,
            "duration_ms": self.duration_ms,
            "retries": self.retries,
            "external_calls": self.external_calls,
            "size_payload": self.size_payload,
        }
