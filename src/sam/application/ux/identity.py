"""identity.py — SAM Production Identity (M11-004).

Menutup gap "approver = string dari client (default 'user')". Sebelum M11-004,
siapa pun yang bisa memanggil POST /ux/decide bisa approve — identitas TIDAK
diverifikasi. Modul ini menambahkan:

  - UserStore : registri user + verifikasi password (hash), dari file JSON
                DI LUAR project (`~/.sam/users.json`). Bukan bagian repo,
                tidak pernah ter-commit.
  - SessionStore : token Bearer acak (in-memory). Login -> token; tiap request
                terproteksi memakai token utk menurunkan identitas NYATA yang
                sudah terverifikasi (bukan string dari browser).

Desain (keputusan M11-004, bertahap):
  - Satu role `operator` utk sekarang (wajib login utk approve). Struktur role
    berupa field, siap diperluas jadi admin/operator/viewer nanti tanpa rombak.
  - Hash password: hashlib.pbkdf2_hmac (SHA-256, salt acak, iterasi 260k)
    — keamanan standar, TANPA dependensi baru.
  - Token sesi: secrets.token_urlsafe (32 byte). In-memory (self-host 1-2 user).
  - Tidak ada plaintext password di disk / log / audit.

Kontrak Service adalah satu-satunya sumber: `verify(username,password)` dan
`authenticate(token)`. Modul TIDAK punya otoritas eksekusi.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import secrets
from pathlib import Path
from typing import Any, Dict, Optional

# Iterasi PBKDF2 (OWASP rekomendasi >= 600k; 260k cukup utk self-host cepat).
_PBKDF2_ITERATIONS = 260_000
_ALGO = "sha256"


def _default_users_file() -> Path:
    """File user di luar project (self-host): ~/.sam/users.json."""
    override = os.environ.get("SAM_USERS_FILE")
    if override:
        return Path(override)
    return Path.home() / ".sam" / "users.json"


def _hash_password(password: str, salt: Optional[bytes] = None) -> Dict[str, str]:
    """Hash password -> {algo, iterations, salt_b64, hash_b64}. Bukan plaintext."""
    if salt is None:
        salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        _ALGO, password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return {
        "algo": _ALGO,
        "iterations": str(_PBKDF2_ITERATIONS),
        "salt": salt.hex(),
        "hash": digest.hex(),
    }


def _verify_password(password: str, record: Dict[str, str]) -> bool:
    """Verifikasi password terhadap hash record. Constant-time via hmac.compare."""
    try:
        salt = bytes.fromhex(record.get("salt", ""))
        iterations = int(record.get("iterations", str(_PBKDF2_ITERATIONS)))
        expected = record.get("hash", "")
        digest = hashlib.pbkdf2_hmac(
            record.get("algo", _ALGO),
            password.encode("utf-8"),
            salt,
            iterations,
        )
        return hmac.compare_digest(digest.hex(), expected)
    except Exception:
        return False


class UserStore:
    """Registri user dari file JSON di luar project.

    Format users.json (contoh; dibuat manual / oleh Van, TIDAK di-repo):
        {
          "users": [
            {"username": "van", "role": "operator",
             "password": "<hash dari _hash_password>"}
          ]
        }
    """

    def __init__(self, path: Optional[str] = None) -> None:
        self._path = Path(path) if path else _default_users_file()
        self._cache: Dict[str, Dict[str, str]] = {}

    @property
    def path(self) -> Path:
        return self._path

    def _load(self) -> Dict[str, Dict[str, str]]:
        """Muat users.json sekali (cache). File hilang/kosong -> dict kosong."""
        if not self._path.exists():
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except Exception:
            return {}
        users: Dict[str, Dict[str, str]] = {}
        for u in data.get("users") or []:
            name = str(u.get("username") or "").strip()
            if name:
                users[name] = {
                    "role": str(u.get("role") or "operator"),
                    "password": u.get("password", ""),
                }
        return users

    def users(self) -> Dict[str, Dict[str, str]]:
        self._cache = self._load()
        return dict(self._cache)

    def verify(self, username: str, password: str) -> Optional[Dict[str, str]]:
        """Return {'username','role'} bila credential valid, else None."""
        users = self.users()
        rec = users.get((username or "").strip())
        if not rec:
            return None
        # rec = {'role': ..., 'password': <dict hash>}; verifikasi hash, bukan rec itu sendiri
        if not _verify_password(password or "", rec.get("password") or {}):
            return None
        return {"username": (username or "").strip(), "role": rec.get("role", "operator")}

    def can_operate(self, role: str) -> bool:
        """Authorization: role operator (dan nanti admin) boleh approve.

        Bertahap: sekarang 1 role; field role siap diperluas. Seluruh cek
        kewenangan approve lewat fungsi ini (single point).
        """
        return (role or "").strip() in ("operator", "admin")


class SessionStore:
    """Token sesi Bearer acak (in-memory). Self-host 1-2 user, tanpa store eksternal.

    - login(user)  -> token baru; simpan token -> user.
    - authenticate(token) -> {'username','role'} utk token valid, else None.
    - logout(token) -> hapus sesi.
    """

    def __init__(self) -> None:
        self._sessions: Dict[str, Dict[str, str]] = {}

    def login(self, user: Dict[str, str]) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = {
            "username": user.get("username", ""),
            "role": user.get("role", "operator"),
        }
        return token

    def authenticate(self, token: Optional[str]) -> Optional[Dict[str, str]]:
        if not token:
            return None
        rec = self._sessions.get(token.strip())
        if not rec:
            return None
        return {"username": rec.get("username", ""), "role": rec.get("role", "operator")}

    def logout(self, token: Optional[str]) -> bool:
        if token and token.strip() in self._sessions:
            del self._sessions[token.strip()]
            return True
        return False
