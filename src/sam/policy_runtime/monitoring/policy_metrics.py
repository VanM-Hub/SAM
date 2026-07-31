"""Policy Metrics — metrik policy (Sprint 209)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.policy_registry import PolicyRegistry


@dataclass(frozen=True)
class PolicyMetricSample:
    """Sampel metrik per unit (immutable)."""
    policy_id: str = ""
    registered: bool = False
    preview_count: int = 0
    external_calls: int = 0


@dataclass(frozen=True)
class PolicyMetrics:
    """Metrik policy agregat (immutable)."""
    total: int = 0
    external_calls: int = 0
    samples: List[PolicyMetricSample] = field(default_factory=list)


class PolicyMetricsCollector:
    """Collector metrik. Read-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def collect(self) -> PolicyMetrics:
        samples = [
            PolicyMetricSample(policy_id=d.id, registered=True,
                               preview_count=0, external_calls=0)
            for d in self._registry.all()
        ]
        return PolicyMetrics(total=len(samples), external_calls=0, samples=samples)
