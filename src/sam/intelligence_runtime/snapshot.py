"""Sprint 266 - Monitoring: snapshot (snapshot runtime immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict

from .health import RuntimeHealth
from .metrics import RuntimeMetrics


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Snapshot status runtime (health + metrics + meta)."""

    health: RuntimeHealth = field(default_factory=RuntimeHealth)
    metrics: RuntimeMetrics = field(default_factory=RuntimeMetrics)
    meta: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "health": self.health.as_dict(),
            "metrics": self.metrics.as_dict(),
            "meta": dict(self.meta),
        }
