# Citizen API - WP-08
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Fasad read-only untuk Citizen Ecosystem. Menjawab pertanyaan komliansi:
#   - Citizen apa saja yang tersedia?        -> list_citizens / all
#   - Capability apa yang dimiliki?           -> capabilities_of
#   - Apa status kesehatannya?                -> health_of
#   - Apa lifecycle-nya?                      -> lifecycle_of
#   - Bagaimana citizen ditemukan?            -> discover
#   - Apa kontrak yang didukung?              -> contracts_of
#   - Apakah citizen compliant?               -> compliance
#   - Mengapa citizen dianggap valid?         -> validity / descriptor.basis
#
# Fasad MURNI read: TIDAK ada register/unregister/activate/deactivate/
# mutate lifecycle di sini (Registry != Authority). Mutasi tetap via registry
# terpisah / authorized actor.

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sam.citizen.registry.registry import CitizenRegistry, RegistryEntry
from sam.citizen.descriptor.descriptor import CitizenDescriptor
from sam.citizen.discovery.engine import (
    CitizenDiscoveryEngine,
    DiscoveryQuery,
    DiscoveryResult,
)
from sam.citizen.health.models import CitizenHealth
from sam.citizen.lifecycle.models import CitizenLifecycle


@dataclass(frozen=True)
class CitizenSummary:
    """Ringkasan citizen untuk konsumsi bagi platform (immutable)."""

    identity_id: str
    kind: str
    name: str
    version: str
    capabilities: Tuple[str, ...] = ()
    contracts: Tuple[str, ...] = ()
    health: str = "unknown"
    lifecycle: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {
            "identity_id": self.identity_id,
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "capabilities": list(self.capabilities),
            "contracts": list(self.contracts),
            "health": self.health,
            "lifecycle": self.lifecycle,
        }


class CitizenAPI:
    """Fasad read-only Citizen Ecosystem (deterministik).

    Tidak memegang otoritas: seluruh metode hanya membaca registry +
    descriptor yang disuntikkan. Tidak ada mutasi.
    """

    def __init__(self, registry: CitizenRegistry,
                 descriptors: Optional[Dict[str, CitizenDescriptor]] = None,
                 healths: Optional[Dict[str, CitizenHealth]] = None,
                 lifecycles: Optional[Dict[str, CitizenLifecycle]] = None):
        self._registry = registry
        self._descriptors: Dict[str, CitizenDescriptor] = dict(descriptors or {})
        self._healths: Dict[str, CitizenHealth] = dict(healths or {})
        self._lifecycles: Dict[str, CitizenLifecycle] = dict(lifecycles or {})
        self._discovery = CitizenDiscoveryEngine(registry)
        self._discovery.attach_descriptors(tuple(self._descriptors.values()))

    # --- inventory (read-only) ---

    @property
    def count(self) -> int:
        return self._registry.count()

    def all(self) -> Tuple[CitizenSummary, ...]:
        return tuple(self._summary(e) for e in self._registry.all())

    def kinds(self) -> Tuple[str, ...]:
        return self._registry.kinds()

    def get(self, identity_id: str) -> Optional[CitizenSummary]:
        entry = self._registry.get(identity_id)
        return self._summary(entry) if entry else None

    # --- attribution (read-only) ---

    def capabilities_of(self, identity_id: str) -> Tuple[str, ...]:
        d = self._descriptors.get(identity_id)
        return d.capabilities if d else ()

    def contracts_of(self, identity_id: str) -> Tuple[str, ...]:
        d = self._descriptors.get(identity_id)
        return d.contracts if d else ()

    def health_of(self, identity_id: str) -> str:
        h = self._healths.get(identity_id)
        return h.level if h else "unknown"

    def lifecycle_of(self, identity_id: str) -> str:
        lc = self._lifecycles.get(identity_id)
        return lc.stage if lc else ""

    def descriptor_of(self, identity_id: str) -> Optional[CitizenDescriptor]:
        return self._descriptors.get(identity_id)

    # --- discovery (deterministic, contract-driven) ---

    def discover(self, kind: str = "", name: str = "", contract: str = "",
                 capability: str = "", identity_id: str = "",
                 healthy_only: bool = False) -> DiscoveryResult:
        return self._discovery.discover(
            DiscoveryQuery(kind=kind, name=name, contract=contract,
                           capability=capability, identity_id=identity_id,
                           healthy_only=healthy_only))

    def by_kind(self, kind: str) -> Tuple[CitizenSummary, ...]:
        return tuple(self._summary(e) for e in self._registry.by_kind(kind))

    # --- validity (explainable: mengapa citizen dianggap valid) ---

    def validity(self, identity_id: str) -> Tuple[bool, Tuple[str, ...]]:
        """Apakah citizen valid? (deskriptor lengkap + basis explainable).

        Mengembalikan (valid, basis). Registry tidak pernah 'mengesahkan'
        otoritas; ini hanya penilaian kelengkapan metadata.
        """
        d = self._descriptors.get(identity_id)
        if d is None:
            return (False, ("no descriptor: citizen not fully described",))
        return (True, d.basis)

    # --- summary helper ---

    def _summary(self, entry: RegistryEntry) -> CitizenSummary:
        d = self._descriptors.get(entry.identity_id)
        h = self._healths.get(entry.identity_id)
        lc = self._lifecycles.get(entry.identity_id)
        return CitizenSummary(
            identity_id=entry.identity_id,
            kind=entry.kind,
            name=entry.name,
            version=entry.identity.version,
            capabilities=d.capabilities if d else (),
            contracts=d.contracts if d else (),
            health=h.level if h else "unknown",
            lifecycle=lc.stage if lc else "",
        )
