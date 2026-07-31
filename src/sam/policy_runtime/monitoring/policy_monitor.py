"""Policy Monitor — pemantauan status policy (Sprint 209)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.policy_registry import PolicyRegistry


@dataclass(frozen=True)
class PolicyStatus:
    """Status policy (immutable)."""
    policy_id: str
    registered: bool = False
    healthy: bool = False

    def __post_init__(self) -> None:
        object.__setattr__(self, "healthy", self.registered)


class PolicyMonitor:
    """Monitor policy. Read-only, deterministik."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def status(self, policy_id: str) -> PolicyStatus:
        return PolicyStatus(policy_id, self._registry.exists(policy_id))

    def all_status(self):
        return [self.status(d.id) for d in self._registry.all()]

    def healthy_count(self) -> int:
        return sum(1 for d in self._registry.all() if self._registry.exists(d.id))
