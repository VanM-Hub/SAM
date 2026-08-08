"""IAM Authenticator — autentikasi kredensial user.

Menutup gap H5 (Program D / MISSION-2D, EA-001-005): menyediakan mekanisme
verifikasi kredensial user yang TIDAK ada sebelumnya (single-operator tanpa
login). Memakai hash constant-time (anti timing attack). Tidak menyimpan /
mengembalikan kredensial plaintext.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Optional

from sam.iam.principal import User, UserStatus
from sam.iam.registry import UserNotFound, UserRegistry


def _utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass(frozen=True)
class AuthenticationResult:
    authenticated: bool
    principal_id: Optional[str] = None
    username: Optional[str] = None
    roles: frozenset[str] = frozenset()
    reason: str = ""
    timestamp: str = ""

    @property
    def ok(self) -> bool:
        return self.authenticated


class Authenticator:
    """Autentikasi user terhadap registry kredensial."""

    def __init__(self, registry: UserRegistry) -> None:
        self._registry = registry

    def authenticate(self, username: str, credential: str) -> AuthenticationResult:
        ts = _utcnow()
        username = username.strip().lower()
        try:
            user = self._registry.get_by_username(username)
        except UserNotFound:
            # Jangan bocorkan apakah username ada (anti user-enumeration)
            return AuthenticationResult(
                authenticated=False, reason="invalid credentials", timestamp=ts,
            )

        if user.status != UserStatus.ACTIVE:
            return AuthenticationResult(
                authenticated=False, username=username, reason="user not active",
                timestamp=ts,
            )

        if user.credential_hash is None:
            return AuthenticationResult(
                authenticated=False, username=username,
                reason="no credential configured", timestamp=ts,
            )

        if not user.credential_hash.verify(credential):
            return AuthenticationResult(
                authenticated=False, username=username,
                reason="invalid credentials", timestamp=ts,
            )

        return AuthenticationResult(
            authenticated=True,
            principal_id=user.user_id,
            username=user.username,
            roles=user.roles,
            reason="ok",
            timestamp=ts,
        )
