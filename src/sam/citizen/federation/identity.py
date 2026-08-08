# Federation Identity - WP-01
# IP-3.4-001 (AO-3.4-001 / ED-3.4-001)
#
# Model identitas Federation - representasi beberapa Citizen Ecosystem yang
# berdaulat (sovereign) saling mengenali. Statis, immutable, deskriptif.
#
# Federation TIDAK memiliki authority. FederationIdentity hanyalah penanda
# relasional: siapa anggota, apa instance, dari mana asalnya. Seluruh
# keputusan tetap LOKAL (Sovereignty First).
#
# Federation Identity != Global Identity: setiap instance mempertahankan
# identitas lokal (local_identity) - Federation hanya menambahkan lapisan
# pengenalan ANTAR ecosystem, tidak pernah menggantikan/menyatukan identitas.

from dataclasses import dataclass
from typing import Dict, Tuple

# Status keanggotaan Federation - TIDAK kontrol, hanya observasi terhadap
# apa yang diumumkan masing-masing ecosystem.
_FED_MEMBER_STATES = ("advertised", "observed", "inactive")


def _state_normalized(state: str) -> str:
    s = state.strip().lower()
    return s if s in _FED_MEMBER_STATES else "observed"


@dataclass(frozen=True)
class FederationIdentity:
    """Identitas Federation itu sendiri (relasional, immutable)."""

    federation_id: str
    name: str = ""
    description: str = ""
    basis: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "federation_id", self.federation_id.strip())
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "description", self.description.strip())
        object.__setattr__(self, "basis", tuple(self.basis))

    def as_dict(self) -> Dict[str, object]:
        return {
            "federation_id": self.federation_id,
            "name": self.name,
            "description": self.description,
            "basis": list(self.basis),
        }


@dataclass(frozen=True)
class FederationMember:
    """Seorang anggota Federation (sebuah Citizen Ecosystem berdaulat).

    - member_id: local id ecosystem di dalam Federation (relasional).
    - local_identity: identitas lokal ecosystem yg dipertahankan (Federation
      Identity != Global Identity - tidak ada penyatuan identitas).
    - endpoint: deskripsi endpoint (metadata OBSERVASIONAL, bukan koneksi).
    - state: status pengenalan (advertised/observed/inactive) - observasi,
      bukan kontrol.
    - sovereignty: konfirmasi bahwa keputusan tetap lokal.
    """

    member_id: str
    local_identity: str = ""
    endpoint: str = ""
    state: str = "observed"
    basis: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "member_id", self.member_id.strip())
        object.__setattr__(self, "local_identity",
                           self.local_identity.strip())
        object.__setattr__(self, "endpoint", self.endpoint.strip())
        object.__setattr__(self, "state", _state_normalized(self.state))
        object.__setattr__(self, "basis", tuple(self.basis))

    def as_dict(self) -> Dict[str, object]:
        return {
            "member_id": self.member_id,
            "local_identity": self.local_identity,
            "endpoint": self.endpoint,
            "state": self.state,
            "basis": list(self.basis),
        }

    @property
    def is_sovereign(self) -> bool:
        """Sovereignty First: anggota selalu mempertahankan keputusan lokal."""
        return True


@dataclass(frozen=True)
class FederationInstance:
    """Instance konkret sebuah Federation (jaringan relasional aktual)."""

    instance_id: str
    federation: FederationIdentity
    members: Tuple[FederationMember, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "instance_id", self.instance_id.strip())
        sorted_members = tuple(sorted(self.members, key=lambda m: m.member_id))
        object.__setattr__(self, "members", sorted_members)

    def as_dict(self) -> Dict[str, object]:
        return {
            "instance_id": self.instance_id,
            "federation": self.federation.as_dict(),
            "members": [m.as_dict() for m in self.members],
        }

    def member_ids(self) -> Tuple[str, ...]:
        return tuple(m.member_id for m in self.members)

    def has_member(self, member_id: str) -> bool:
        return any(m.member_id == member_id for m in self.members)
