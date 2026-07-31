"""Policy Health — kesehatan runtime policy (Sprint 209)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.policy_registry import PolicyRegistry


@dataclass(frozen=True)
class PolicyHealth:
    """Kesehatan policy (immutable)."""
    total: int = 0
    healthy_policy: int = 0

    @property
    def healthy(self) -> bool:
        return self.healthy_policy == self.total


class PolicyHealthCheck:
    """Health check policy. Read-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def check(self) -> PolicyHealth:
        total = self._registry.count()
        healthy = sum(1 for d in self._registry.all() if self._registry.exists(d.id))
        return PolicyHealth(total=total, healthy_policy=healthy)
