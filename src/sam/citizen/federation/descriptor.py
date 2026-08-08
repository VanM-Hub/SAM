# Federation Descriptor - WP-04
# IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
#
# Deskripsi capability Federation (DEKLARATIF, bukan eksekusi).
#
# Descriptor hanya menyatakan apa yang mampu/sediakan sebuah member:
#   - capability: daftar nama capability yang diiklankan
#   - contracts: contract yang didukung (untuk pertukaran capability)
#   - version: versi member/descriptor
#   - compatibility: hasil assessment kompatibilitas (opsional)
#   - certification: hasil sertifikasi (opsional)
#
# Descriptor != Contract Execution: sepenuhnya deklaratif - tidak menyimpan
# implementasi, tidak memanggil, tidak mengeksekusi contract.

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class FederationDescriptor:
    """Deskripsi capability sebuah Federation member (immutable)."""

    member_id: str
    capability: Tuple[str, ...] = ()
    contracts: Tuple[str, ...] = ()
    version: str = ""
    compatibility: Tuple[Tuple[str, object], ...] = ()
    certification: Tuple[str, object] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "member_id", self.member_id.strip())
        object.__setattr__(self, "capability", tuple(self.capability))
        object.__setattr__(self, "contracts", tuple(self.contracts))
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "compatibility",
                           tuple(self.compatibility))
        object.__setattr__(self, "certification", tuple(self.certification))

    def as_dict(self) -> Dict[str, object]:
        return {
            "member_id": self.member_id,
            "capability": list(self.capability),
            "contracts": list(self.contracts),
            "version": self.version,
            "compatibility": list(self.compatibility),
            "certification": list(self.certification),
        }

    def has_capability(self, capability: str) -> bool:
        return capability in self.capability

    def supports_contract(self, contract: str) -> bool:
        return contract in self.contracts

    @property
    def is_declarative(self) -> bool:
        """Descriptor selalu deskriptif - tidak pernah eksekusi."""
        return True


def build_federation_descriptor(
    member_id: str,
    *,
    capability: Tuple[str, ...] = (),
    contracts: Tuple[str, ...] = (),
    version: str = "",
    compatibility: Tuple[Tuple[str, object], ...] = (),
    certification: Tuple[str, object] = (),
) -> FederationDescriptor:
    """Builder deskriptor Federation (deklaratif, immutable)."""
    return FederationDescriptor(
        member_id=member_id,
        capability=tuple(capability),
        contracts=tuple(contracts),
        version=version,
        compatibility=tuple(compatibility),
        certification=tuple(certification),
    )
