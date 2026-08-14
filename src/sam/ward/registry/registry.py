# Ward Registry - M13-002 (Repository Pattern)
#
# Registry Ward HANYA menyimpan identitas + metadata + entrustment, dan
# melayani discovery. Registry TIDAK boleh: execute, observe, restart,
# delete, mutate. (Registry != Authority; WardRegistration != mutation
# permission - M13-003/M13-010.)
#
# WardIdentity IMMUTABLE - tidak pernah berubah setelah dibuat.
# Operasi:
#   register         - daftarkan Ward (eksplisit, unik ward_id)
#   get              - ambil Ward by ward_id (None bila tidak ada)
#   list             - daftar semua (atau filter by ward_type / status)
#   update_metadata  - ubah metadata deskriptif (identity TETAP immutable)
#   revoke           - set status revoked (identity tetap ada, akses dicabut)
#
# Secure default (fail-closed): registrasi TANPA entrustment tetap mencatat
# Ward, tapi authorization (lihat Entrustment) menolak apapun sampai konsen
# dari Owner ada. Revoked Ward -> langsung kehilangan akses.

from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from sam.ward.identity.models import Ward, WardIdentity
from sam.ward.entrustment.models import Entrustment


class WardConflictError(ValueError):
    """Registrasi gagal karena ward_id sudah terdaftar (konflik unik)."""


class WardNotFoundError(KeyError):
    """Ward tidak ditemukan."""


@dataclass(frozen=True)
class WardEntry:
    """Satu entri registry (Ward + metadata registrasi, immutable)."""

    ward: Ward
    registered_at: str = ""
    origin: str = ""

    @property
    def ward_id(self) -> str:
        return self.ward.ward_id

    @property
    def ward_type(self) -> str:
        return self.ward.ward_type

    @property
    def name(self) -> str:
        return self.ward.name

    def as_dict(self) -> Dict[str, object]:
        return {
            "ward": self.ward.as_dict(),
            "registered_at": self.registered_at,
            "origin": self.origin,
        }


class WardRepository:
    """Repository Ward: penyimpanan identitas/metadata + discovery.

    Murni read/write data terstruktur. TIDAK ada eksekusi, TIDAK ada mutasi
    eksternal, TIDAK ada authority. Segala aksi terhadap Ward harus melewati
    AuthorizationGate + canonical execution di lapisan lain.
    """

    def __init__(self) -> None:
        self._by_id: Dict[str, WardEntry] = {}
        self._entrustments: Dict[str, Entrustment] = {}  # ward_id -> entrustment

    # --- registrasi (eksplisit; tidak ada hidden registration) ---

    def register(self, identity: WardIdentity, *, owner: "WardOwner | None" = None,
                 access_scope: "WardAccessScope | None" = None,
                 metadata: "WardMetadata | None" = None,
                 entrustment: Optional[Entrustment] = None,
                 registered_at: str = "", origin: str = "",
                 overwrite: bool = False) -> WardEntry:
        """Daftarkan Ward secara eksplisit.

        `overwrite=True` memperbolehkan mengganti metadata entri yang sudah
        ada (identitas TETAP immutable). Default: duplikat -> WardConflictError.
        """
        if self._by_id.get(identity.ward_id) is not None and not overwrite:
            raise WardConflictError("ward already registered: {}".format(identity.ward_id))

        from sam.ward.identity.models import Ward, WardAccessScope, WardOwner, WardMetadata
        ward = Ward(
            identity=identity,
            owner=owner if owner is not None else WardOwner(owner_id=""),
            access_scope=access_scope if access_scope is not None else WardAccessScope(),
            metadata=metadata if metadata is not None else WardMetadata(),
        )
        self._by_id[identity.ward_id] = WardEntry(
            ward=ward, registered_at=registered_at, origin=origin)
        if entrustment is not None:
            self._entrustments[identity.ward_id] = entrustment
        return self._by_id[identity.ward_id]

    def get(self, ward_id: str) -> Optional[Ward]:
        """Ambil Ward by ward_id (None bila tidak ada)."""
        entry = self._by_id.get(ward_id)
        return entry.ward if entry else None

    def get_entry(self, ward_id: str) -> Optional[WardEntry]:
        """Ambil WardEntry lengkap (Ward + metadata registrasi)."""
        return self._by_id.get(ward_id)

    def list(self, *, ward_type: Optional[str] = None,
             status: Optional[str] = None) -> List[Ward]:
        """Daftar Ward, filter opsional by ward_type / status."""
        result = []
        for entry in self._by_id.values():
            w = entry.ward
            if ward_type is not None and w.ward_type != ward_type:
                continue
            if status is not None and w.status != status:
                continue
            result.append(w)
        # urutan deterministik by ward_id
        result.sort(key=lambda w: w.ward_id)
        return result

    def update_metadata(self, ward_id: str, *, description: Optional[str] = None,
                        data: Optional[Tuple[Tuple[str, str], ...]] = None) -> Ward:
        """Perbarui metadata deskriptif Ward. Identity TETAP immutable."""
        entry = self._by_id.get(ward_id)
        if entry is None:
            raise WardNotFoundError(ward_id)
        w = entry.ward
        from sam.ward.identity.models import WardMetadata
        md = w.metadata
        new_desc = description if description is not None else md.description
        new_data = data if data is not None else md.data
        new_ward = Ward(identity=w.identity, owner=w.owner,
                        access_scope=w.access_scope,
                        metadata=WardMetadata(description=new_desc, data=new_data),
                        status=w.status)
        # replace entry (preserve registered_at/origin)
        self._by_id[ward_id] = WardEntry(ward=new_ward,
                                         registered_at=entry.registered_at,
                                         origin=entry.origin)
        return new_ward

    def revoke(self, ward_id: str, *, revoked_at: str = "") -> Ward:
        """Cabut akses Ward (status -> revoked). Identity tetap ada."""
        entry = self._by_id.get(ward_id)
        if entry is None:
            raise WardNotFoundError(ward_id)
        w = entry.ward
        new_ward = Ward(identity=w.identity, owner=w.owner,
                        access_scope=w.access_scope, metadata=w.metadata,
                        status="revoked")
        self._by_id[ward_id] = WardEntry(ward=new_ward,
                                         registered_at=entry.registered_at,
                                         origin=entry.origin)
        # revoke entrustment bila ada
        ent = self._entrustments.get(ward_id)
        if ent is not None and not ent.revoked_at:
            self._entrustments[ward_id] = Entrustment(
                ward_id=ent.ward_id, owner_id=ent.owner_id,
                allowed_capabilities=ent.allowed_capabilities,
                access_scope=ent.access_scope,
                approval_policy=ent.approval_policy,
                created_at=ent.created_at, revoked_at=revoked_at or ent.created_at)
        return new_ward

    def get_entrustment(self, ward_id: str) -> Optional[Entrustment]:
        """Entrustment (konsen Owner) untuk Ward ini, bila ada."""
        return self._entrustments.get(ward_id)

    def set_entrustment(self, entrustment: Entrustment) -> None:
        """Tetapkan / perbarui entrustment untuk Ward (konsen owner)."""
        self._entrustments[entrustment.ward_id] = entrustment

    def count(self) -> int:
        return len(self._by_id)
