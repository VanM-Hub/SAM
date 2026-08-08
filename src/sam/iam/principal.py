"""IAM Principal — model identitas user & role.

Menutup gap H5 (Program D / MISSION-2D, EA-001-005): representasi identity
user yang TIDAK ada sebelumnya (default single-operator tanpa login).

Immutable dataclass/Pydantic, mengikuti pola DTO di repo (`ADR-023`).
Kredensial disimpan sebagai hash, bukan plaintext.
"""

from __future__ import annotations

import hashlib
import hmac
import secrets
from dataclasses import dataclass, field
from typing import Optional


def _constant_time_equal(left: bytes, right: bytes) -> bool:
    """Bandingkan dua nilai dengan constant-time compare (anti timing attack)."""
    return hmac.compare_digest(left, right)


@dataclass(frozen=True)
class CredentialHash:
    """Hash kredensial (token) user — storage-safe, bukan plaintext."""

    salt_hex: str = field(default_factory=lambda: secrets.token_hex(16))
    digest_hex: str = ""
    algorithm: str = "sha256-pbkdf2"

    def __post_init__(self) -> None:
        if not self.digest_hex:
            raise ValueError("CredentialHash memerlukan digest_hex (gunakan UserRegistry.set_credential)")

    def verify(self, candidate: Optional[str]) -> bool:
        """Verifikasi kredensial mentah terhadap hash ini (constant-time)."""
        if candidate is None:
            return False
        salt = bytes.fromhex(self.salt_hex)
        digest = hashlib.pbkdf2_hmac(
            "sha256", candidate.encode("utf-8"), salt, iterations=120_000,
        )
        return _constant_time_equal(digest.hex().encode("ascii"), self.digest_hex.encode("ascii"))

    @staticmethod
    def create(raw: str) -> "CredentialHash":
        """Buat hash baru dari kredensial mentah."""
        salt = secrets.token_hex(16)
        digest = hashlib.pbkdf2_hmac(
            "sha256", raw.encode("utf-8"), bytes.fromhex(salt), iterations=120_000,
        ).hex()
        return CredentialHash(salt_hex=salt, digest_hex=digest)


class UserStatus:
    ACTIVE = "active"
    DISABLED = "disabled"
    LOCKED = "locked"


@dataclass(frozen=True)
class Role:
    """Role (grup permission) untuk RBAC."""

    role_id: str
    name: str
    permissions: frozenset[str] = frozenset()
    description: str = ""

    def __post_init__(self) -> None:
        if not self.role_id:
            raise ValueError("role_id tidak boleh kosong")


@dataclass(frozen=True)
class Principal:
    """Identitas pelaku akses — user (subject untuk AccessControl)."""

    principal_id: str
    username: str
    roles: frozenset[str] = frozenset()

    @property
    def subject(self) -> str:
        """Nilai subject yang kompatibel dengan AccessControl (RBAC)."""
        return self.principal_id


@dataclass(frozen=True)
class User:
    """User di registry IAM."""

    user_id: str
    username: str
    roles: frozenset[str] = frozenset()
    status: str = UserStatus.ACTIVE
    display_name: str = ""
    credential_hash: Optional[CredentialHash] = None

    def to_principal(self) -> Principal:
        return Principal(
            principal_id=self.user_id,
            username=self.username,
            roles=self.roles,
        )
