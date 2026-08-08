"""IAM Registry — user store.

Menyimpan/kelola user & kredensial (hash). Murni in-memory (single-node,
sesuai scope Program D). Tidak mengubah runtime existing.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from sam.iam.principal import CredentialHash, User, UserStatus


class UserAlreadyExists(Exception):
    """Username sudah terdaftar."""


class UserNotFound(Exception):
    """User tidak ditemukan."""


class UserRegistry:
    """Registry user IAM (in-memory store).

    - Tidak menyimpan kredensial plaintext — hanya `CredentialHash`.
    - Tidak mengubah runtime/approval/guardian existing.
    """

    def __init__(self) -> None:
        self._users: Dict[str, User] = {}        # by user_id
        self._by_username: Dict[str, str] = {}   # username -> user_id

    # ---- CRUD ----

    def create_user(
        self,
        username: str,
        roles: Optional[frozenset[str]] = None,
        display_name: str = "",
    ) -> User:
        """Buat user baru (tanpa kredensial; set via `set_credential`)."""
        username = username.strip().lower()
        if not username:
            raise ValueError("username tidak boleh kosong")
        if username in self._by_username:
            raise UserAlreadyExists(username)
        user_id = f"usr-{len(self._users) + 1}"
        user = User(
            user_id=user_id,
            username=username,
            roles=roles or frozenset(),
            display_name=display_name,
        )
        self._users[user_id] = user
        self._by_username[username] = user_id
        return user

    def set_credential(self, username: str, raw_credential: str) -> None:
        """Set/timpa kredensial user (disimpan sebagai hash)."""
        user = self.get_by_username(username)
        updated = User(
            user_id=user.user_id,
            username=user.username,
            roles=user.roles,
            status=user.status,
            display_name=user.display_name,
            credential_hash=CredentialHash.create(raw_credential),
        )
        self._users[user.user_id] = updated

    def get(self, user_id: str) -> User:
        if user_id not in self._users:
            raise UserNotFound(user_id)
        return self._users[user_id]

    def get_by_username(self, username: str) -> User:
        username = username.strip().lower()
        user_id = self._by_username.get(username)
        if not user_id:
            raise UserNotFound(username)
        return self._users[user_id]

    def assign_role(self, username: str, role_id: str) -> User:
        user = self.get_by_username(username)
        new_roles = frozenset(set(user.roles) | {role_id})
        updated = User(
            user_id=user.user_id,
            username=user.username,
            roles=new_roles,
            status=user.status,
            display_name=user.display_name,
            credential_hash=user.credential_hash,
        )
        self._users[user.user_id] = updated
        return updated

    def disable(self, username: str) -> User:
        return self._set_status(username, UserStatus.DISABLED)

    def activate(self, username: str) -> User:
        return self._set_status(username, UserStatus.ACTIVE)

    def _set_status(self, username: str, status: str) -> User:
        user = self.get_by_username(username)
        updated = User(
            user_id=user.user_id,
            username=user.username,
            roles=user.roles,
            status=status,
            display_name=user.display_name,
            credential_hash=user.credential_hash,
        )
        self._users[user.user_id] = updated
        return updated

    def list_users(self) -> List[User]:
        return sorted(self._users.values(), key=lambda u: u.username)

    def has_credential(self, username: str) -> bool:
        try:
            return self.get_by_username(username).credential_hash is not None
        except UserNotFound:
            return False

    def count(self) -> int:
        return len(self._users)
