# Citizen Descriptor - WP-03
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Deskriptor menjelaskan SEBUAH citizen: metadata terstruktur, explainable,
# dan contract-driven. Semua read-only.
#
# - descriptor completeness: deskriptor harus lengkap (identity + summary +
#   kontrak + capability + health + lifecycle + metadata) untuk "valid".
# - explainable metadata: deskriptor membawa `basis`/`evidence` alasan
#   mengapa citizen dianggap valid.
# - contract-driven lookup: setiap citizen mengekspos kontrak yang didukung
#   (contracts), yang dipakai discovery untuk mencocokkan kebutuhan.

from dataclasses import dataclass
from typing import Dict, Optional, Tuple

from sam.citizen.identity.models import CitizenIdentity


@dataclass(frozen=True)
class CitizenDescriptor:
    """Deskripsi lengkap seorang citizen (immutable).

    identity      : identitas (immutable, unique)
    summary       : ringkasan satu kalimat
    contracts     : kontrak yang didukung (tuple[str])
    capabilities  : nama-nama capability yang dimiliki (tuple[str])
    health_status : ringkasan kesehatan ("healthy"/"degraded"/"unavailable"/"unknown")
    lifecycle_stage: tahap lifecycle ("registered"/"discovered"/...)
    metadata      : metadata tambahan kv (immutable tuple)
    basis         : alasan/evidence deskriptor dianggap valid (tuple[str])
    """

    identity: CitizenIdentity
    summary: str = ""
    contracts: Tuple[str, ...] = ()
    capabilities: Tuple[str, ...] = ()
    health_status: str = "unknown"
    lifecycle_stage: str = ""
    metadata: Tuple[Tuple[str, str], ...] = ()
    basis: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "summary", self.summary.strip())
        object.__setattr__(self, "health_status",
                           self.health_status.strip() or "unknown")

    @property
    def identity_id(self) -> str:
        return self.identity.identity_id

    @property
    def kind(self) -> str:
        return self.identity.kind

    def supports_contract(self, contract: str) -> bool:
        return contract in self.contracts

    def has_capability(self, capability: str) -> bool:
        return capability in self.capabilities

    def is_complete(self) -> bool:
        """Deskriptor dianggap lengkap bila punya identitas + minimal satu
        kontrak + basis (explainable). Ini untuk check 'descriptor
        completeness'."""
        return bool(self.identity.identity_id and self.contracts and self.basis)

    def as_dict(self) -> Dict[str, object]:
        return {
            "identity": self.identity.as_dict(),
            "summary": self.summary,
            "contracts": list(self.contracts),
            "capabilities": list(self.capabilities),
            "health_status": self.health_status,
            "lifecycle_stage": self.lifecycle_stage,
            "metadata": list(self.metadata),
            "basis": list(self.basis),
            "is_complete": self.is_complete(),
        }


def build_descriptor(
    identity: CitizenIdentity,
    *,
    summary: str = "",
    contracts: Tuple[str, ...] = (),
    capabilities: Tuple[str, ...] = (),
    health_status: str = "unknown",
    lifecycle_stage: str = "",
    metadata: Tuple[Tuple[str, str], ...] = (),
    basis: Tuple[str, ...] = (),
) -> CitizenDescriptor:
    """Pabrik deskriptor dengan basis default (explainable)."""
    if not basis:
        basis = ("descriptor provided", "identity immutable",
                 "capability-first model")
    return CitizenDescriptor(
        identity=identity, summary=summary, contracts=contracts,
        capabilities=capabilities, health_status=health_status,
        lifecycle_stage=lifecycle_stage, metadata=metadata, basis=basis,
    )
