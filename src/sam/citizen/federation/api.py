# Federation API - WP-07
# IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
#
# Fasad READ-ONLY Federation. Menjawab:
#   - discover()       - siapa yang dikenal
#   - describe()       - deskripsi lengkap seorang member
#   - capabilities()   - capability apa yang diiklankan (bukan eksekusi)
#   - health()         - kesehatan observasional seluruh Federation
#
# Tidak ada verb untuk: connect/execute/invoke/control/approve/authorize.
# Federation selamanya tanpa authority, registry = metadata.

from typing import Dict, Optional, Sequence, Tuple

from sam.citizen.federation.identity import (
    FederationMember,
    FederationIdentity,
    FederationInstance,
)
from sam.citizen.federation.registry import FederationRegistry
from sam.citizen.federation.discovery import FederationDiscovery
from sam.citizen.federation.descriptor import FederationDescriptor
from sam.citizen.federation.capability_exchange import (
    CapabilityAdvertisement,
    CapabilityExchange,
)
from sam.citizen.federation.health import (
    FederationHealth,
    FederationHealthAssessor,
)


class FederationAPI:
    """Fasad read-only Federation (discover/describe/capabilities/health)."""

    def __init__(self, registry: FederationRegistry = None,
                 descriptors=None, healths: Dict[str, str] = None,
                 federation: FederationIdentity = None) -> None:
        self._registry = registry or FederationRegistry()
        self._descriptors = tuple(descriptors or ())
        self._healths = dict(healths or {})
        self._federation = federation
        self._discovery = FederationDiscovery(self._registry, self._descriptors)
        self._exchange = CapabilityExchange(self._descriptors)
        self._health = FederationHealthAssessor()

    # --- discover() ---

    def discover(self, capability: str = None) -> Tuple[str, ...]:
        """Member yang dikenal (opsional: filter oleh iklan capability)."""
        if capability is not None:
            return self._discovery.discover_by_capability(capability)
        return self._discovery.discover_all()

    # --- describe() ---

    def describe(self, member_id: str) -> Optional[FederationMember]:
        return self._registry.get(member_id)

    def descriptor(self, member_id: str) -> Optional[FederationDescriptor]:
        for d in self._descriptors:
            if getattr(d, "member_id", None) == member_id:
                return d
        return None

    # --- capabilities() --- (advertisement, bukan eksekusi)

    def capabilities(self, member_id: str = None) -> object:
        if member_id is not None:
            return self._exchange.advertises(member_id)
        return self._exchange.exchanged()

    def advertised(self) -> Tuple[str, ...]:
        """Semua capability yang diiklankan seluruh member."""
        result = set()
        for m in self._discovery.discover_all():
            result.update(self._exchange.advertises(m).capabilities)
        return tuple(sorted(result))

    # --- health() --- (observasional)

    def health(self) -> FederationHealth:
        known = self._discovery.discover_all()
        health_map = {}
        for mid in known:
            if mid in self._healths:
                health_map[mid] = self._healths[mid]
            else:
                health_map[mid] = "unknown"
        return self._health.assess(health_map)

    # --- helpers ---

    def instance(self) -> FederationInstance:
        federation = self._federation or FederationIdentity("fed-default")
        members = self._registry.all()
        return FederationInstance(
            instance_id="fed-inst-" + federation.federation_id,
            federation=federation,
            members=members,
        )
