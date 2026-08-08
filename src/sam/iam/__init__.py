"""SAM IAM — User Identity & Access Management.

Menutup gap H5 (Priority P2, Program D / MISSION-2D) yang tercatat di
EA-001-005: "Tidak ada user authentication/authorization (IAM) — default
single-operator tanpa login; REST/server perlu otentikasi untuk produksi."

Desain (konservatif terhadap constraint EA-002):
- Modul IAM berdiri sendiri (stand-alone) sebagai capability baru.
- TIDAK mengubah responsibility runtime existing (approval gate, guardian,
  runtime_kernel) — integrasi ke lapisan tersebut adalah keputusan arsitektur
  terpisah (di luar scope H5).
- Authorization memakai pola RBAC yang kompatibel dengan model
  `runtime_kernel.runtime_security.AccessControl` (subject/resource/permission).
- Kredensial disimpan sebagai hash (BUKAN plaintext).
"""

from __future__ import annotations

from sam.iam.authorizer import (
    AccessDecision,
    Authorizer,
    Permission,
    Resource,
    Role,
    RoleAssignments,
)
from sam.iam.authenticator import AuthenticationResult, Authenticator
from sam.iam.audit import AccessAuditRecord, AccessAuditLog
from sam.iam.principal import CredentialHash, Principal, User, UserStatus
from sam.iam.registry import UserAlreadyExists, UserNotFound, UserRegistry

__all__ = [
    "AccessDecision",
    "AccessAuditLog",
    "AccessAuditRecord",
    "AuthenticationResult",
    "Authenticator",
    "Authorizer",
    "CredentialHash",
    "Permission",
    "Principal",
    "Resource",
    "Role",
    "RoleAssignments",
    "User",
    "UserAlreadyExists",
    "UserNotFound",
    "UserRegistry",
    "UserStatus",
]
