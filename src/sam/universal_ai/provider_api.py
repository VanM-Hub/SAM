"""AI Provider API - WP-08 (MISSION-5.1 / IP-5.1-001).

API untuk mengakses seluruh capability foundation. Tetap berada pada bounded
context AI Provider; tidak mengambil alih Governance atau Execution.
"""
from __future__ import annotations

from typing import Optional, Tuple

from .capability_model import AICapabilityKind
from .provider_descriptor import AIModelDescriptor, ProviderDescriptor
from .provider_discovery import AIProviderDiscovery, DiscoveryResult
from .provider_health import AIProviderHealthCheck, ProviderHealth
from .provider_identity import ProviderIdentity, ProviderStatus
from .provider_registry import AIProviderRegistry


class AIProviderAPI:
    """API publik bounded context Universal AI Provider Foundation."""

    def __init__(
        self,
        registry: Optional[AIProviderRegistry] = None,
        discovery: Optional[AIProviderDiscovery] = None,
        health: Optional[AIProviderHealthCheck] = None,
    ) -> None:
        self.registry = registry or AIProviderRegistry()
        self.discovery = discovery or AIProviderDiscovery(self.registry)
        self._healthcheck = health or AIProviderHealthCheck()

    # Registry
    def register(self, identity: ProviderIdentity, availability: bool = False):
        return self.registry.register(identity, availability=availability)

    def lookup(self, provider_id: str) -> Optional[ProviderIdentity]:
        return self.registry.lookup(provider_id)

    def list_providers(self, status: Optional[ProviderStatus] = None) -> Tuple[ProviderIdentity, ...]:
        return self.registry.list(status=status)

    # Discovery
    def discover(self, kind: Optional[AICapabilityKind] = None) -> Tuple[DiscoveryResult, ...]:
        if kind is None:
            all_results = []
            for p in self.registry.list():
                all_results.append(DiscoveryResult(provider_id=p.provider_id))
            return tuple(all_results)
        return self.discovery.discover_capability(kind)

    def discover_models(self, provider_id: Optional[str] = None) -> Tuple[AIModelDescriptor, ...]:
        return self.discovery.discover_models(provider_id=provider_id)

    def set_descriptors(self, descriptors: Tuple[ProviderDescriptor, ...]) -> None:
        self.discovery.set_descriptors(descriptors)

    # Health
    def health(self, provider_id: str) -> Optional[ProviderHealth]:
        identity = self.registry.lookup(provider_id)
        if identity is None:
            return None
        return self._healthcheck.assess(provider_id)
