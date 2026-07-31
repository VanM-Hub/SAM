"""Sprint 266 - Monitoring: metrics (metrik runtime immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class RuntimeMetrics:
    """Metrik aplikasi (counter deterministik)."""

    counters: Dict[str, int] = field(default_factory=dict)

    def with_counter(self, name: str, value: int = 1) -> "RuntimeMetrics":
        counters = dict(self.counters)
        counters[name] = counters.get(name, 0) + value
        return RuntimeMetrics(counters=counters)

    def get(self, name: str) -> int:
        return self.counters.get(name, 0)

    def as_dict(self) -> dict:
        return {"counters": dict(self.counters)}
