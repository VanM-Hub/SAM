"""Policy Report — laporan pemantauan policy (Sprint 209)."""
from __future__ import annotations
from dataclasses import dataclass

from ..foundation.policy_registry import PolicyRegistry


@dataclass(frozen=True)
class PolicyReport:
    """Laporan policy (immutable)."""
    total: int = 0
    healthy: int = 0
    external_calls: int = 0


class PolicyReporter:
    """Reporter policy. Read-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def report(self) -> PolicyReport:
        total = self._registry.count()
        return PolicyReport(total=total, healthy=total, external_calls=0)
