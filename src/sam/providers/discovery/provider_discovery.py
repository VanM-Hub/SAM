"""Provider Discovery — penemuan provider (read-only).

Sprint 150 — Provider Discovery.
Menemukan provider terdaftar dan kapabilitasnya. Tidak invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..base.provider_descriptor import ProviderDescriptor
from ..base.provider_capability import ProviderCapability
from ..registry.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class DiscoveryCriterion:
    """Kriteria penemuan provider (immutable)."""
    provider_type: str = ""
    capability: str = ""
    operation: str = ""

    def matches(self, desc: ProviderDescriptor, caps: List[ProviderCapability]) -> bool:
        if self.provider_type and desc.provider_type != self.provider_type:
            return False
        if self.capability:
            if not any(c.capability_id == self.capability for c in caps):
                return False
        if self.operation:
            if not any(c.supports(self.operation) for c in caps):
                return False
        return True


@dataclass(frozen=True)
class DiscoveryResult:
    """Hasil penemuan (immutable)."""
    criterion: DiscoveryCriterion
    provider_ids: List[str] = field(default_factory=list)


class ProviderDiscovery:
    """Penemuan provider dari registry. Read-only, deterministik."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def discover(self, criterion: DiscoveryCriterion = None) -> DiscoveryResult:
        criterion = criterion or DiscoveryCriterion()
        found = []
        for pid in self._registry.list_ids():
            desc = self._registry.get(pid)
            caps = self._registry.get_capabilities(pid)
            if desc and criterion.matches(desc, caps):
                found.append(pid)
        return DiscoveryResult(criterion=criterion, provider_ids=found)

    def all(self) -> List[str]:
        return list(self._registry.list_ids())

    def of_type(self, provider_type: str) -> List[str]:
        return self.discover(DiscoveryCriterion(provider_type=provider_type)).provider_ids
