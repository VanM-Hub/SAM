# Citizen Identity Model - WP-01
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Identitas Citizen adalah primer, immutable, unik, dan equal (Citizen Equality).
# - immutable: identity_id TIDAK pernah berubah setelah dibuat.
# - unique: setiap citizen teridentifikasi by stable id + kind.
# - equal: TIDAK ada "privileged citizen"; semua entitas (runtime, provider,
#   workflow, mission, ...) adalah jenis (kind) citizen yang setara.
#
# Murni data (DTO), read-only, deterministik.

import hashlib
from dataclasses import dataclass
from typing import Dict, Optional, Tuple

# Jenis (kind) citizen yang dikenal. Nilai NORMAL = string konsisten,
# TIDAK boleh "privileged" di level model.
_KINDS = ("runtime", "provider", "workflow", "mission", "policy", "capability",
          "service", "extension", "unknown")


def _kind_normalized(kind: str) -> str:
    """Normalisasi kind -> lower-case konsisten, default 'unknown'."""
    k = kind.strip().lower()
    return k if k in _KINDS else "unknown"


@dataclass(frozen=True)
class CitizenIdentity:
    """Identitas immutable seorang citizen.

    - identity_id: primer, dibuat from canonical seed (stable).
    - kind: jenis citizen (runtime/provider/workflow/mission/...).
    - name: nama yang mudah dibaca (readable), bukan identitas.
    - version: versi citizen.
    - namespace: ruang nama opsional (isolasi antar domain).
    - labels: metadata kv opsional (immutable tuple).
    """

    identity_id: str
    kind: str
    name: str = ""
    version: str = ""
    namespace: str = ""
    labels: Tuple[Tuple[str, str], ...] = ()

    def __post_init__(self) -> None:
        # normalisasi kind via object.__setattr__ (frozen dataclass).
        object.__setattr__(self, "kind", _kind_normalized(self.kind))
        object.__setattr__(self, "name", self.name.strip())
        object.__setattr__(self, "version", self.version.strip())
        object.__setattr__(self, "namespace", self.namespace.strip())

    @property
    def is_known(self) -> bool:
        """Apakah kind citizen dikenal platform (bukan 'unknown')."""
        return self.kind != "unknown"

    @property
    def display(self) -> str:
        """Nama tampilan ringkas: 'name@kind'."""
        if self.name:
            return "{}@{}".format(self.name, self.kind)
        return "{}@{}".format(self.identity_id, self.kind)

    def as_dict(self) -> Dict[str, object]:
        return {
            "identity_id": self.identity_id,
            "kind": self.kind,
            "name": self.name,
            "version": self.version,
            "namespace": self.namespace,
            "labels": list(self.labels),
        }

    @classmethod
    def new(cls, kind: str, name: str, *, version: str = "",
            namespace: str = "", labels: Tuple[Tuple[str, str], ...] = (),
            seed: Optional[str] = None) -> "CitizenIdentity":
        """Buat identitas baru dengan identity_id deterministik.

        identity_id = sha1(kind|name|version|namespace)[:12], prefiks 'cit-'.
        Semantic id (versus random) memastikan citizen yang sama -> id sama
        (deterministik, reconcilable).
        """
        canonical = "|".join([kind, name.strip(), version.strip(),
                              namespace.strip()])
        if seed:
            canonical = canonical + "|" + seed
        digest = hashlib.sha1(canonical.encode("utf-8")).hexdigest()[:12]
        return cls(identity_id="cit-" + digest, kind=kind, name=name,
                   version=version, namespace=namespace, labels=labels)

    def with_labels(self, labels: Tuple[Tuple[str, str], ...]) -> "CitizenIdentity":
        """Salin identitas dengan labels baru (identity_id TETAP sama)."""
        return CitizenIdentity(
            identity_id=self.identity_id, kind=self.kind, name=self.name,
            version=self.version, namespace=self.namespace, labels=labels,
        )

    def matches_kind(self, kind: str) -> bool:
        """Apakah identitas ini berjenis `kind` (equal, case-insensitive)?"""
        return self.kind == _kind_normalized(kind)
