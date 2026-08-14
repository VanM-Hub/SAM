# Ward Authorization Boundary - M13-010 (Governance Boundary - security gate)
#
# Ini GATE KEAMANAN UTAMA untuk Ward.
#
#   Observation:
#       Boleh jika Ward registered + access granted (entrustment aktif +
#       capability observation diizinkan).
#
#   Mutation:
#       WAJIB Ward access + capability permission + mission + policy +
#       approval + canonical execution. Tidak ada jalur langsung ke connector.
#
#   Revoked Ward:
#       revoke -> observation blocked + mutation blocked.
#
# Integritas: TIDAK ada connector yang menyimpan authority sendiri. Connector
# hanyalah infrastructure adapter; segala keputusan izin ada di boundary ini
# (dan di ApprovalGate canonical untuk mutation).

from dataclasses import dataclass
from typing import Optional

from sam.ward.registry.registry import WardRepository
from sam.ward.entrustment.models import Entrustment


@dataclass(frozen=True)
class AuthorizationResult:
    """Hasil pemeriksaan izin (verdict + alasan + detail)."""

    allowed: bool
    reason: str
    ward_id: str = ""
    capability: str = ""
    requires_approval: bool = False

    def as_dict(self) -> dict:
        return {
            "allowed": self.allowed,
            "reason": self.reason,
            "ward_id": self.ward_id,
            "capability": self.capability,
            "requires_approval": self.requires_approval,
        }


# Capability yang bersifat observation (read-only).
_OBSERVATION = ("observe", "investigate", "diagnose", "recommend",
                "verify", "learn", "report")
# Capability yang bersifat mutation (harus approval + canonical).
_MUTATION = ("protect", "mutate", "restart", "write", "delete")


class WardGovernanceBoundary:
    """Gate otorisasi untuk seluruh aksi terhadap Ward.

    Murni keputusan izin (deterministik). TIDAK mengeksekusi apa pun.
    Boundary ini dipakai OLEH lapisan application/runtime SEBELUM connector
    dipanggil; connector tidak pernah menilai izinnya sendiri.
    """

    def __init__(self, repository: WardRepository) -> None:
        self._repo = repository

    # --- helpers ---

    def _entrustment(self, ward_id: str) -> Optional[Entrustment]:
        return self._repo.get_entrustment(ward_id)

    def _classified(self, capability: str) -> str:
        c = capability.strip().lower()
        if c in _OBSERVATION:
            return "observation"
        if c in _MUTATION:
            return "mutation"
        return "unknown"

    # --- public API ---

    def can_observe(self, ward_id: str, capability: str = "observe") -> AuthorizationResult:
        """Cek izin observation (read-only).

        Boleh bila: Ward terdaftar + status active + entrustment aktif +
        capability observation diizinkan.
        """
        ward = self._repo.get(ward_id)
        if ward is None:
            return AuthorizationResult(False, "ward not registered", ward_id, capability)

        if ward.is_revoked:
            return AuthorizationResult(False, "ward revoked - access blocked",
                                       ward_id, capability)

        ent = self._entrustment(ward_id)
        if ent is None or not ent.is_active:
            return AuthorizationResult(False, "no active entrustment (consent missing)",
                                       ward_id, capability)

        cap = capability.strip().lower()
        if not ent.allows(cap) and "observe" not in ent.allowed_capabilities and \
           cap not in _OBSERVATION:
            return AuthorizationResult(False, "capability not granted",
                                       ward_id, capability)

        return AuthorizationResult(True, "observation granted", ward_id,
                                   capability, requires_approval=False)

    def can_mutate(self, ward_id: str, capability: str = "protect") -> AuthorizationResult:
        """Cek izin mutation.

        Wajib: Ward active + entrustment aktif + capability mutation diizinkan
        + approval policy required. Selalu requires_approval=True (nanti dicek
        di ApprovalGate canonical - boundary ini hanya menyatakan kebutuhannya).
        """
        ward = self._repo.get(ward_id)
        if ward is None:
            return AuthorizationResult(False, "ward not registered", ward_id, capability)

        if ward.is_revoked:
            return AuthorizationResult(False, "ward revoked - mutation blocked",
                                       ward_id, capability)

        ent = self._entrustment(ward_id)
        if ent is None or not ent.is_active:
            return AuthorizationResult(False, "no active entrustment (consent missing)",
                                       ward_id, capability)

        cap = capability.strip().lower()
        mutation_granted = (cap in ent.allowed_capabilities or
                            "protect" in ent.allowed_capabilities)
        if not mutation_granted:
            return AuthorizationResult(False, "mutation capability not granted",
                                       ward_id, capability)

        if not ent.approval_policy.required:
            return AuthorizationResult(False, "mutation requires approval policy",
                                       ward_id, capability)

        # Mutation selalu lewat approval (canonical) - boundary menyatakan
        # kebutuhan approval, bukan menyetujuinya.
        return AuthorizationResult(True, "mutation authorized (requires approval)",
                                   ward_id, capability, requires_approval=True)

    def check(self, ward_id: str, capability: str) -> AuthorizationResult:
        """Dispatch general: observation vs mutation vs unknown."""
        kind = self._classified(capability)
        if kind == "observation":
            return self.can_observe(ward_id, capability)
        if kind == "mutation":
            return self.can_mutate(ward_id, capability)
        return AuthorizationResult(False, "unknown capability: {}".format(capability),
                                   ward_id, capability)
