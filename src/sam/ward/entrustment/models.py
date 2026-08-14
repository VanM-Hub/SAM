# Ward Entrustment Model - M13-003 (Entrustment / Consent)
#
# Setiap Ward harus mempunyai relasi:
#     Owner
#       ↓
#     Entrustment
#       ↓
#     Ward
#
# Entrustment adalah KONSENSI EKSPLISIT yang diberikan Owner kepada SAM
# atas sebuah Ward. Ini yang MEMISAHKAN:
#   - Registered Ward  (SAM kenal objeknya)  -- dari WardRegistry
#   - Authorized action (apa yang boleh dilakukan) -- dari Entrustment
#
# Prinsip M13-010: Registered Ward != Permission to mutate. Authorization
# (entrustment) menentukan apa yang boleh dilakukan. Tanpa entrustment yang
# valid & aktif, observation pun ditolak (revoked -> blocked).
#
# Murni data (DTO), immutable.
from dataclasses import dataclass, field
from typing import Dict, Tuple

# Capability yang dikenal pada entrustment. Observation selalu read-only;
# mutation selalu lewat approval + policy + canonical execution (M13-010).
_OBSERVATION_CAPS = ("observe", "investigate", "diagnose", "recommend", "verify", "learn")
_MUTATION_CAPS = ("protect", "mutate")


def _caps_normalized(caps: Tuple[str, ...]) -> Tuple[str, ...]:
    """Normalisasi capability -> lower-case, tanpa duplikasi, urutan stabil."""
    seen = []
    for c in caps:
        c = c.strip().lower()
        if c and c not in seen:
            seen.append(c)
    return tuple(seen)


@dataclass(frozen=True)
class ApprovalPolicy:
    """Kebijakan persetujuan untuk mutation pada Ward ini.

    Mutation SELALU melewati approval (canonical). Policy ini menentukan
    mode default; tidak pernah menonaktifkan approval (M13-007, M13-010).
    """

    required: bool = True              # approval wajib (selalu True utk mutation)
    approver_role: str = "operator"    # role yang berhak menyetujui
    timeout_seconds: int = 3600        # waktu entrustment valid (default 1 jam)

    def as_dict(self) -> Dict[str, object]:
        return {
            "required": self.required,
            "approver_role": self.approver_role,
            "timeout_seconds": self.timeout_seconds,
        }


@dataclass(frozen=True)
class Entrustment:
    """Konsensi eksplisit Owner atas Ward.

    - ward_id: Ward yang dipercayakan.
    - owner_id: siapa yang mempercayakan.
    - allowed_capabilities: capability yang diizinkan (observe/investigate/...).
    - access_scope: cakupan akses (deskripsi resource target).
    - approval_policy: kebijakan persetujuan (mutation wajib approve).
    - created_at / revoked_at: tanda waktu konsensi.
    """

    ward_id: str
    owner_id: str
    allowed_capabilities: Tuple[str, ...] = field(default_factory=tuple)
    access_scope: str = ""
    approval_policy: ApprovalPolicy = field(default_factory=ApprovalPolicy)
    created_at: str = ""
    revoked_at: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "allowed_capabilities",
                           _caps_normalized(self.allowed_capabilities))

    @property
    def is_active(self) -> bool:
        return not self.revoked_at

    def allows(self, capability: str) -> bool:
        """Apakah entrustment mengizinkan capability (read/mutation)?"""
        cap = capability.strip().lower()
        if cap in _OBSERVATION_CAPS:
            # observation boleh bila konsen diberikan & tidak revoked
            return self.is_active and ("observe" in self.allowed_capabilities or
                                       cap in self.allowed_capabilities)
        if cap in _MUTATION_CAPS:
            # mutation wajib approval (policy.required) + capability diizinkan
            return (self.is_active and
                    self.approval_policy.required and
                    (cap in self.allowed_capabilities or
                     "protect" in self.allowed_capabilities))
        return self.is_active and cap in self.allowed_capabilities

    def as_dict(self) -> Dict[str, object]:
        return {
            "ward_id": self.ward_id,
            "owner_id": self.owner_id,
            "allowed_capabilities": list(self.allowed_capabilities),
            "access_scope": self.access_scope,
            "approval_policy": self.approval_policy.as_dict(),
            "created_at": self.created_at,
            "revoked_at": self.revoked_at,
        }
