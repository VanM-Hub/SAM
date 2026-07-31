"""Policy Runtime Report — laporan runtime integrasi (Sprint 211)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.policy_registry import PolicyRegistry
from .policy_runtime_pipeline import INTEGRATION_ROUTE


@dataclass(frozen=True)
class PolicyRuntimeReport:
    """Laporan runtime integrasi (immutable)."""
    total_policy: int = 0
    route: List[str] = field(default_factory=list)
    external_calls: int = 0
    ready: bool = False


class PolicyRuntimeReporter:
    """Reporter runtime integrasi. Read-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def report(self) -> PolicyRuntimeReport:
        return PolicyRuntimeReport(
            total_policy=self._registry.count(),
            route=list(INTEGRATION_ROUTE),
            external_calls=0,
            ready=self._registry.count() > 0,
        )
