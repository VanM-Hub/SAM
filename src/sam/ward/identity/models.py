# Ward Domain Model - M13-001 (External Subject / Ward Foundation)
#
# Ward = entitas eksternal yang DIPERCAYAKAN (entrusted) oleh Owner kepada SAM.
# Ward BUKAN Citizen. Citizen = internal governed entity; Ward = externally
# entrusted entity. Keduanya adalah SUBJECT yang bisa dioperasikan oleh
# Universal Governance Engine, namun berada di lapisan yang berbeda dan TIDAK
# dicampur.
#
# Prinsip (aturan 1-17 M13):
#   - Domain TIDAK mengetahui GitHub/Docker/PostgreSQL (Clean Architecture).
#   - WardIdentity immutable.
#   - Registration != authority: mendaftarkan Ward hanya membuat SAM mengenal
#     objek; authorization menentukan apa yang boleh dilakukan.
#   - Murni data (DTO), read-only, deterministik.
import hashlib
from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple

# Jenis awal Ward yang dikenal. Nilai NORMAL = string konsisten.
_WARD_TYPES = (
    "application",
    "service",
    "repository",
    "container",
    "database",
    "host",
    "filesystem",
    "external_api",
    "unknown",
)

# Status siklus hidup Ward.
_WARD_STATUSES = ("active", "revoked")


def _normalize(value: str, allowed: Tuple[str, ...], default: str) -> str:
    v = value.strip().lower()
    return v if v in allowed else default


@dataclass(frozen=True)
class WardIdentity:
    """Identitas immutable seorang Ward.

    - ward_id: primer, deterministik dari seed (stable).
    - ward_type: jenis Ward (repository/container/database/...).
    - name: nama yang mudah dibaca (readable), bukan identitas.
    - namespace: ruang nama opsional.
    - labels: metadata kv opsional (immutable).
    """

    ward_id: str
    ward_type: str
    name: str = ""
    namespace: str = ""
    labels: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        object.__setattr__(self, "ward_type", _normalize(self.ward_type, _WARD_TYPES, "unknown"))
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "namespace", self.namespace.strip())

    @property
    def is_known(self) -> bool:
        """Apakah jenis Ward dikenal platform (bukan 'unknown')."""
        return self.ward_type != "unknown"

    @property
    def display(self) -> str:
        """Nama tampilan ringkas: 'name@ward_type'."""
        if self.name:
            return "{}@{}".format(self.name, self.ward_type)
        return "{}@{}".format(self.ward_id, self.ward_type)

    def as_dict(self) -> Dict[str, object]:
        return {
            "ward_id": self.ward_id,
            "ward_type": self.ward_type,
            "name": self.name,
            "namespace": self.namespace,
            "labels": list(self.labels),
        }

    @classmethod
    def new(cls, ward_type: str, name: str, *, namespace: str = "",
            labels: Tuple[Tuple[str, str], ...] = (),
            seed: Optional[str] = None) -> "WardIdentity":
        """Buat identitas baru dengan ward_id deterministik (sha1 from seed)."""
        canonical_seed = seed if seed else "{}|{}|{}".format(
            ward_type.strip().lower(), name.strip(), namespace)
        digest = hashlib.sha1(canonical_seed.encode("utf-8")).hexdigest()[:16]
        return cls(
            ward_id="ward-" + digest,
            ward_type=ward_type,
            name=name.strip(),
            namespace=namespace.strip(),
            labels=labels,
        )


@dataclass(frozen=True)
class WardOwner:
    """Pemilik entrustment: siapa (Owner) yang mempercayakan Ward kepada SAM."""

    owner_id: str
    owner_name: str = ""
    owner_role: str = ""

    def as_dict(self) -> Dict[str, object]:
        return {
            "owner_id": self.owner_id,
            "owner_name": self.owner_name,
            "owner_role": self.owner_role,
        }


@dataclass(frozen=True)
class WardAccessScope:
    """Ruang lingkup akses yang diberikan Owner kepada SAM atas Ward.

    access_scope = deskripsi terbatas (immutable) tentang APA yang boleh
    dijangkau. Ini adalah DATA, bukan authority: tetap harus melewati
    approval & policy & canonical execution untuk mutation.
    """

    scope: str = ""                 # deskripsi cakupan (e.g. "github:VanM-Hub/SAM")
    resource: str = ""              # resource target eksternal
    endpoints: Tuple[str, ...] = ()  # endpoint yang diizinkan (read)

    def as_dict(self) -> Dict[str, object]:
        return {
            "scope": self.scope,
            "resource": self.resource,
            "endpoints": list(self.endpoints),
        }


@dataclass(frozen=True)
class WardMetadata:
    """Metadata opsional Ward (deskriptif, mutable hanya via update_metadata)."""

    description: str = ""
    data: Tuple[Tuple[str, str], ...] = ()

    def as_dict(self) -> Dict[str, object]:
        return {
            "description": self.description,
            "data": list(self.data),
        }


@dataclass(frozen=True)
class Ward:
    """Model agregat Ward (identity + owner + access + status + metadata).

    WardIdentity IMMUTABLE. Owner/access/metadata lain immutable via frozen
    dataclass; perubahan terbatas (update_metadata) dilakukan dengan membuat
    instance baru di registry (bukan mutasi di sini).
    """

    identity: WardIdentity
    owner: WardOwner = field(default_factory=lambda: WardOwner(owner_id=""))
    access_scope: WardAccessScope = field(default_factory=WardAccessScope)
    metadata: WardMetadata = field(default_factory=WardMetadata)
    status: str = "active"

    def __post_init__(self) -> None:
        object.__setattr__(self, "status", _normalize(self.status, _WARD_STATUSES, "active"))

    @property
    def ward_id(self) -> str:
        return self.identity.ward_id

    @property
    def ward_type(self) -> str:
        return self.identity.ward_type

    @property
    def name(self) -> str:
        return self.identity.name

    @property
    def is_active(self) -> bool:
        return self.status == "active"

    @property
    def is_revoked(self) -> bool:
        return self.status == "revoked"

    def as_dict(self) -> Dict[str, object]:
        return {
            "identity": self.identity.as_dict(),
            "owner": self.owner.as_dict(),
            "access_scope": self.access_scope.as_dict(),
            "metadata": self.metadata.as_dict(),
            "status": self.status,
        }
