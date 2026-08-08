# Citizen Discovery Engine - WP-05
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Discovery bersifat DETERMINISTIK dan EXPLICIT (kontrak-driven lookup).
# - deterministik: hasil pencarian bergantung HANYA pada registry + query
#   (no random, no waktu, no urutan implisit).
# - contract-driven lookup: citizen ditemukan via KONTRAK yang didukung &
#   CAPABILITY yang dimiliki (bukan by kebetulan / urutan registrasi).
# - no implicit discovery: discovery selalu butuh query eksplisit (kind/name/
#   contract/capability). Tidak ada "ambil semua tanpa kriteria" sebagai
#   satu-satunya jalur; all() hanya untuk inventory eksplisit.

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sam.citizen.registry.registry import CitizenRegistry, RegistryEntry
from sam.citizen.descriptor.descriptor import CitizenDescriptor


@dataclass(frozen=True)
class DiscoveryQuery:
    """Query discovery eksplisit & deterministik.

    Semua bidang opsional; bila kosong berarti tidak difilter pada dimensi itu.
    Minimal harus ada SATU kriteria (kind/name/contract/capability/identity_id)
    agar discovery berjalan (no implicit discovery).
    """

    kind: str = ""
    name: str = ""
    contract: str = ""
    capability: str = ""
    identity_id: str = ""
    healthy_only: bool = False

    def has_criteria(self) -> bool:
        return any((self.kind, self.name, self.contract,
                    self.capability, self.identity_id)) or self.healthy_only


@dataclass(frozen=True)
class DiscoveryResult:
    """Hasil discovery: daftar citizen yang cocok + penjelasan (basis)."""

    matches: Tuple[RegistryEntry, ...]
    query: DiscoveryQuery
    basis: Tuple[str, ...] = ()

    def count(self) -> int:
        return len(self.matches)

    def as_dict(self) -> Dict[str, object]:
        return {
            "count": self.count(),
            "matches": [e.as_dict() for e in self.matches],
            "query": {
                "kind": self.query.kind,
                "name": self.query.name,
                "contract": self.query.contract,
                "capability": self.query.capability,
                "identity_id": self.query.identity_id,
                "healthy_only": self.query.healthy_only,
            },
            "basis": list(self.basis),
        }


class CitizenDiscoveryEngine:
    """Menemukan citizen dari registry secara deterministik & contract-driven.

    Discovery murni query: TIDAK mengaktifkan, TIDAK mengubah lifecycle,
    TIDAK menjalankan capability. (Registry/Discovery != Authority.)
    """

    def __init__(self, registry: CitizenRegistry,
                 descriptors: Optional[Dict[str, CitizenDescriptor]] = None):
        self._registry = registry
        # map identity_id -> descriptor (health status untuk filter healthy_only)
        self._descriptors: Dict[str, CitizenDescriptor] = dict(descriptors or {})

    def attach_descriptors(self, descriptors: Tuple[CitizenDescriptor, ...]) -> None:
        for d in descriptors:
            self._descriptors[d.identity_id] = d

    def discover(self, query: DiscoveryQuery) -> DiscoveryResult:
        """Jalankan discovery eksplisit. Menolak query kosong (implicit)."""
        if not query.has_criteria():
            raise ValueError("discovery requires explicit criteria "
                             "(no implicit discovery)")

        candidates: List[RegistryEntry] = list(self._registry.all())
        reasons: List[str] = []

        if query.identity_id:
            entry = self._registry.get(query.identity_id)
            candidates = [entry] if entry else []
            reasons.append("by identity_id")
        if query.kind:
            bucket = set(e.identity_id for e in self._registry.by_kind(query.kind))
            candidates = [e for e in candidates if e.identity_id in bucket]
            reasons.append("by kind={}".format(query.kind))
        if query.name:
            bucket = set(e.identity_id for e in self._registry.by_name(query.name))
            candidates = [e for e in candidates if e.identity_id in bucket]
            reasons.append("by name={}".format(query.name))
        if query.contract:
            candidates = [e for e in candidates
                          if self._contract_of(e.identity_id, query.contract)]
            reasons.append("by contract={}".format(query.contract))
        if query.capability:
            candidates = [e for e in candidates
                          if self._capability_of(e.identity_id, query.capability)]
            reasons.append("by capability={}".format(query.capability))
        if query.healthy_only:
            candidates = [e for e in candidates
                          if self._source_available(e.identity_id)]
            reasons.append("healthy_only (source available)")

        # urut by identity_id -> deterministik
        matches = tuple(sorted(candidates, key=lambda e: e.identity_id))
        basis = ("discovery deterministic",
                 "contract-driven lookup",
                 "; ".join(reasons) if reasons else "explicit query")
        return DiscoveryResult(matches=matches, query=query, basis=(basis,))

    def _contract_of(self, identity_id: str, contract: str) -> bool:
        d = self._descriptors.get(identity_id)
        return bool(d and d.supports_contract(contract))

    def _capability_of(self, identity_id: str, capability: str) -> bool:
        d = self._descriptors.get(identity_id)
        return bool(d and d.has_capability(capability))

    def _source_available(self, identity_id: str) -> bool:
        """Citizen dianggap 'source available' bila deskriptor ada dan
        status kesehatannya bukan 'unavailable'."""
        d = self._descriptors.get(identity_id)
        if d is None:
            return True  # tidak ada data kesehatan -> tidak dikecualikan
        return d.health_status != "unavailable"
