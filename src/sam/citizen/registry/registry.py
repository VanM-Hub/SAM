# Citizen Registry - WP-02
# IP-3.3-001 (AO-3.3-001 / ED-3.3-001)
#
# Registry hanya MENYIMPAN identitas + METADATA, dan melayani DISCOVERY.
# Registry TIDAK boleh: mengaktifkan/mematikan citizen, mengatur lifecycle,
# menjalankan capability. (Registry != Authority, ED-3.3-001 Engineering Risks #2)
#
# - unique identity: identity_id harus unik (tidak boleh duplikat).
# - registry consistency: operasi konsisten & deterministik.
# - hidden registration = dilarang: semua registrasi eksplisit via register().

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sam.citizen.identity.models import CitizenIdentity


class RegistryConflictError(ValueError):
    """Registrasi gagal karena identity_id sudah terdaftar (konflik unik)."""


@dataclass(frozen=True)
class RegistryEntry:
    """Satu entri registry (identity + metadata terkait, immutable)."""

    identity: CitizenIdentity
    registered_at: str
    origin: str = ""           # deklarasi/pemanggil yang mendaftarkan
    annotations: Tuple[Tuple[str, str], ...] = ()

    @property
    def identity_id(self) -> str:
        return self.identity.identity_id

    @property
    def kind(self) -> str:
        return self.identity.kind

    @property
    def name(self) -> str:
        return self.identity.name

    def as_dict(self) -> Dict[str, object]:
        return {
            "identity": self.identity.as_dict(),
            "registered_at": self.registered_at,
            "origin": self.origin,
            "annotations": list(self.annotations),
        }


class CitizenRegistry:
    """Registry citizen: penyimpanan identitas + discovery berbasis kontrak.

    Murni read/write data terstruktur. Tidak ada eksekusi, tidak ada lifecycle
    mutation, tidak ada activation.
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, RegistryEntry] = {}
        self._by_kind: Dict[str, List[str]] = {}
        self._by_name: Dict[str, List[str]] = {}

    # --- registrasi (eksplisit - tidak ada hidden registration) ---

    def register(self, identity: CitizenIdentity, *, registered_at: str = "",
                 origin: str = "", annotations: Tuple[Tuple[str, str], ...] = (),
                 overwrite: bool = False) -> RegistryEntry:
        """Daftarkan citizen secara eksplisit.

        `overwrite=True` memperbolehkan mengganti metadata entri yang sudah
        ada (identitas TETAP immutable; identity_id tidak berubah).
        Default: konflik duplikat -> RegistryConflictError (unique identity).
        """
        entry = RegistryEntry(identity=identity, registered_at=registered_at,
                              origin=origin, annotations=annotations)
        existing = self._by_id.get(identity.identity_id)
        if existing is not None and not overwrite:
            raise RegistryConflictError(
                "identity already registered: {}".format(identity.identity_id))
        if existing is not None and overwrite:
            # hapus pendaftaran lama di indeks kind/name sebelum menimpa
            self._unindex(existing)
        self._by_id[identity.identity_id] = entry
        self._index(entry)
        return entry

    def unregister(self, identity_id: str) -> bool:
        """Hapus citizen dari registry (identitas tetap valid, hanya tidak
        lagi terdaftar). Mengembalikan True bila terhapus."""
        entry = self._by_id.pop(identity_id, None)
        if entry is None:
            return False
        self._unindex(entry)
        return True

    # --- query (deterministic, read-only) ---

    def get(self, identity_id: str) -> Optional[RegistryEntry]:
        """Ambil entri by identity_id (None bila tidak ada)."""
        return self._by_id.get(identity_id)

    def has(self, identity_id: str) -> bool:
        return identity_id in self._by_id

    def count(self) -> int:
        return len(self._by_id)

    def all(self) -> Tuple[RegistryEntry, ...]:
        """Semua entri, urut by identity_id (deterministik)."""
        return tuple(sorted(self._by_id.values(), key=lambda e: e.identity_id))

    def by_kind(self, kind: str) -> Tuple[RegistryEntry, ...]:
        """Semua citizen dari satu jenis (equal, tidak ada privileged)."""
        ids = self._by_kind.get(kind.strip().lower(), ())
        return tuple(self._by_id[i] for i in sorted(ids))

    def by_name(self, name: str) -> Tuple[RegistryEntry, ...]:
        matched = self._by_name.get(name.strip(), ())
        return tuple(self._by_id[i] for i in sorted(matched))

    def kinds(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_kind.keys()))

    def identity_ids(self) -> Tuple[str, ...]:
        return tuple(sorted(self._by_id.keys()))

    def as_dict(self) -> Dict[str, object]:
        return {
            "count": self.count(),
            "entries": [e.as_dict() for e in self.all()],
        }

    # --- internal indexing ---

    def _index(self, entry: RegistryEntry) -> None:
        self._by_kind.setdefault(entry.kind, []).append(entry.identity_id)
        if entry.name:
            self._by_name.setdefault(entry.name, []).append(entry.identity_id)

    def _unindex(self, entry: RegistryEntry) -> None:
        for bucket, key in ((self._by_kind, entry.kind),
                            (self._by_name, entry.name)):
            if key in bucket:
                lst = bucket[key]
                if entry.identity_id in lst:
                    lst.remove(entry.identity_id)
                if not lst:
                    del bucket[key]
