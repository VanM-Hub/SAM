"""RuntimeMetrics (Sprint 269).

Program D - Runtime Services & Deployment.
Metrics runtime (counter, immutable snapshot).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class RuntimeMetrics:
    """Metrics runtime (immutable)."""
    name: str
    counters: Dict[str, int] = field(default_factory=dict)

    def get(self, key: str, default: int = 0) -> int:
        return self.counters.get(key, default)

    def as_dict(self) -> dict:
        return {"name": self.name, "counters": dict(self.counters)}
