"""RuntimeSummary (Sprint 271).

Program D - Runtime Services & Deployment.
Ringkasan runtime (immutable).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List


@dataclass(frozen=True)
class RuntimeSummary:
    """Ringkasan runtime (immutable)."""
    services: List[str] = field(default_factory=list)
    count: int = 0
    ready: bool = False
    version: str = "27.0.0"

    def as_dict(self) -> dict:
        return {
            "services": list(self.services),
            "count": self.count,
            "ready": self.ready,
            "version": self.version,
        }


def build_runtime_summary(registry: Any) -> RuntimeSummary:
    return RuntimeSummary(
        services=registry.names(),
        count=registry.count(),
        ready=registry.all_ready(),
    )
