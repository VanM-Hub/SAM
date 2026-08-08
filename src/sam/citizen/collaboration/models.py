# Citizen Collaboration Model - WP-11
# IP-3.3-002 (AO-3.3-001 / ED-3.3-001 2nd cycle)
#
# Model hubungan & kolaborasi antar-Citizen TANPA privilege. Sebuah
# kolaborasi adalah relasi antara dua atau lebih citizen yang:
#   - bersifat equal (tidak ada pihak superior/inferior)
#   - eksplisit (tidak ada implicit collaboration)
#   - read-only di level model (collaboration != orchestration)
#   - deterministik (id, role, channel stabil)
#
# Murni representasi data (DTO), immutable. Tidak ada eksekusi action.

import hashlib
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Peran (role) dalam kolaborasi - SEMUA equal, tidak ada pemimpin/bawahan.
# Tidak ada role "owner"/"master"/"controller" (no privileged).
_COLLAB_ROLES = ("initiator", "participant", "peer", "observer")


def _role_normalized(role: str) -> str:
    """Normalisasi role -> lower-case konsisten, default 'peer'."""
    r = role.strip().lower()
    return r if r in _COLLAB_ROLES else "peer"


@dataclass(frozen=True)
class CollaborationChannel:
    """Saluran interaksi kolaborasi (deskriptif, bukan eksekusi)."""

    name: str
    description: str = ""
    direction: str = "bidirectional"   # "one-way" | "bidirectional"
    basis: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "description", self.description.strip())
        d = self.direction.strip().lower()
        if d not in ("one-way", "bidirectional"):
            d = "bidirectional"
        object.__setattr__(self, "direction", d)

    def as_dict(self) -> Dict[str, object]:
        return {
            "name": self.name,
            "description": self.description,
            "direction": self.direction,
            "basis": list(self.basis),
        }

    def is_bidirectional(self) -> bool:
        return self.direction == "bidirectional"


@dataclass(frozen=True)
class CollaborationRole:
    """Peran seorang citizen dalam kolaborasi (equal, non-privileged)."""

    citizen_identity_id: str
    role: str = "peer"

    def __post_init__(self) -> None:
        object.__setattr__(self, "citizen_identity_id",
                           self.citizen_identity_id.strip())
        object.__setattr__(self, "role", _role_normalized(self.role))

    def as_dict(self) -> Dict[str, object]:
        return {
            "citizen_identity_id": self.citizen_identity_id,
            "role": self.role,
        }


@dataclass(frozen=True)
class CollaborationSpec:
    """Spesifikasi relasi kolaborasi antar citizen (immutable).

    - collaboration_id: deterministik (sha1 dari set citizen ids + channel).
    - roles: peran tiap citizen (equal).
    - channel: saluran interaksi.
    - shared_capabilities: capability yang di-share/berpartisipasi.
    - is_enabled: status eksplisit (default True; bila False = tidak aktif).
    """

    collaboration_id: str
    roles: Tuple[CollaborationRole, ...]
    channel: CollaborationChannel = CollaborationChannel("default")
    shared_capabilities: Tuple[str, ...] = ()
    is_enabled: bool = True
    basis: Tuple[str, ...] = ()

    def __post_init__(self) -> None:
        # urutkan roles berdasarkan citizen_identity_id (deterministik).
        sorted_roles = tuple(sorted(self.roles,
                                    key=lambda r: r.citizen_identity_id))
        object.__setattr__(self, "roles", sorted_roles)
        object.__setattr__(self, "shared_capabilities",
                           tuple(self.shared_capabilities))

    @property
    def citizen_ids(self) -> Tuple[str, ...]:
        return tuple(r.citizen_identity_id for r in self.roles)

    def as_dict(self) -> Dict[str, object]:
        return {
            "collaboration_id": self.collaboration_id,
            "roles": [r.as_dict() for r in self.roles],
            "channel": self.channel.as_dict(),
            "shared_capabilities": list(self.shared_capabilities),
            "is_enabled": self.is_enabled,
            "basis": list(self.basis),
        }

    def has_citizen(self, identity_id: str) -> bool:
        return any(r.citizen_identity_id == identity_id for r in self.roles)

    @classmethod
    def new(cls, roles: Tuple[CollaborationRole, ...],
            channel_name: str = "default", *,
            shared_capabilities: Tuple[str, ...] = (),
            is_enabled: bool = True) -> "CollaborationSpec":
        """Buat spesifikasi kolaborasi dengan id deterministik.

        id = sha1(sorted citizen_ids | channel)[:12], prefiks 'col-'.
        """
        r = roles
        ids = sorted(x.citizen_identity_id for x in r)
        canonical = "|".join(ids) + "|" + channel_name.strip()
        digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:12]
        return cls(
            collaboration_id="col-" + digest,
            roles=r,
            channel=CollaborationChannel(channel_name.strip()),
            shared_capabilities=tuple(shared_capabilities),
            is_enabled=is_enabled,
            basis=("collaboration is equal", "explicit roles",
                   "no privilege", "deterministic id"),
        )


@dataclass(frozen=True)
class CollaborationLink:
    """Tautan kolaborasi lengkap (spec + status kegiatan)."""

    spec: CollaborationSpec
    active: bool = True
    note: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {
            "collaboration_id": self.spec.collaboration_id,
            "active": self.active,
            "note": self.note,
            "spec": self.spec.as_dict(),
        }


def is_privilege_free(spec: CollaborationSpec) -> bool:
    """Apakah kolaborasi bebas privilege?

    True bila tidak ada role owner/master/controller dan SEMUA peran termasuk
    role known yang equal.
    """
    if any(r.role not in _COLLAB_ROLES for r in spec.roles):
        return False
    forbidden = ("owner", "master", "controller", "admin", "supervisor")
    role_names = {r.role for r in spec.roles}
    return not (role_names & set(forbidden))
