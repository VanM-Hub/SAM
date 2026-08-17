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

    def create_user(
        self, username: str, password: str, role: str = "operator"
    ) -> Dict[str, str]:
        """Buat user baru & simpan ke file (register akun dari UI).

        - username dipakai sebagai key (trim).
        - bila username SUDAH ada -> raise ValueError (409 di route).
        - password TIDAK pernah disimpan plaintext; di-hash pbkdf2 (iter tinggi).
        - menulis SEMUA user (lama + baru) ke `users.json` tanpa menimpa yang lain.
        - file berada DI LUAR project (default ~/.sam/users.json), tidak pernah
          di-commit; dibuat otomatis bila belum ada.

        Return dict {'username','role'} milik user baru.
        """
        name = (username or "").strip()
        if not name:
            raise ValueError("username wajib diisi")
        if not password or len(password) < 6:
            raise ValueError("password minimal 6 karakter")

        # baca data file saat ini (tidak hanya cache) utk jumlah record akurat
        data: Dict[str, list] = {"users": []}
        try:
            if self._path.exists():
                with open(self._path, "r", encoding="utf-8") as f:
                    data = json.load(f)
        except Exception:
            data = {"users": []}
        data = data if isinstance(data, dict) else {"users": []}
        data.setdefault("users", [])

        # cek duplikat (case-sensitive, sesuai key login)
        existing = {str(u.get("username") or "").strip() for u in data["users"]}
        if name in existing:
            raise ValueError(f"username '{name}' sudah ada")

        record = {
            "username": name,
            "role": role or "operator",
            "password": _hash_password(password),
        }
        data["users"].append(record)

        self._path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        self._cache = self._load()  # segarkan cache
        return {"username": name, "role": record["role"]}

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


def _now_epoch() -> float:
    import time
    return time.time()


_SESSION_TTL = 60 * 60  # 1 jam default (env SAM_SESSION_TTL override)


class SessionStore:
    """Token sesi Bearer acak (in-memory). Self-host 1-2 user, tanpa store eksternal.

    M12-011 Identity Hardening menambah:
      - Session TTL : token kedaluwarsa (default 1 jam; env SAM_SESSION_TTL).
      - Revocation   : sesi bisa di-revoke (logout eksplisit / admin), revoked DENIED.
      - CSRF token   : per sesi; utk mode cookie, mutasi wajib kirim X-CSRF-Token.
      - authenticate() menolak anonymous/expired/revoked/unknown (forged).

    - login(user)       -> token baru {created_at, csrf}.
    - authenticate(token)-> {'username','role'} utk token valid, else None.
    - logout(token)     -> hapus sesi.
    - revoke(token)     -> tandai sesi revoked (langsung tak valid).
    - csrf_for / verify_csrf -> utk proteksi CSRF pada mutasi cookie.
    """

    def __init__(self, ttl: Optional[int] = None) -> None:
        self._ttl = (
            ttl if ttl is not None
            else int(os.environ.get("SAM_SESSION_TTL", str(_SESSION_TTL)))
        )
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._revoked: Dict[str, float] = {}

    def login(self, user: Dict[str, str]) -> str:
        token = secrets.token_urlsafe(32)
        self._sessions[token] = {
            "username": user.get("username", ""),
            "role": user.get("role", "operator"),
            "created_at": _now_epoch(),
            "csrf": secrets.token_urlsafe(32),
        }
        return token

    def authenticate(self, token: Optional[str]) -> Optional[Dict[str, str]]:
        if not token:
            return None
        tok = token.strip()
        rec = self._sessions.get(tok)
        # unknown / tidak ada = forged -> DENIED
        if not rec:
            return None
        # revoked -> DENIED
        if tok in self._revoked:
            return None
        # expired -> DENIED (juga bersihkan sesi yg kedaluwarsa)
        if _now_epoch() - rec.get("created_at", 0) > self._ttl:
            self._sessions.pop(tok, None)
            return None
        return {"username": rec.get("username", ""), "role": rec.get("role", "operator")}

    def logout(self, token: Optional[str]) -> bool:
        if token and token.strip() in self._sessions:
            del self._sessions[token.strip()]
            return True
        return False

    def revoke(self, token: Optional[str]) -> bool:
        """Revoke sesi: langsung tak valid (authenticate menolak)."""
        if token and token.strip() in self._sessions:
            self._revoked[token.strip()] = _now_epoch()
            self._sessions.pop(token.strip(), None)
            return True
        return False

    def revoke_user(self, username: str) -> int:
        """Revoke semua sesi milik user. Return jumlah yang di-revoke."""
        targets = [t for t, r in self._sessions.items() if r.get("username") == username]
        for t in targets:
            self.revoke(t)
        return len(targets)

    def csrf_for(self, token: Optional[str]) -> Optional[str]:
        if not token:
            return None
        rec = self._sessions.get(token.strip())
        return rec.get("csrf") if rec else None

    def verify_csrf(self, token: Optional[str], provided: Optional[str]) -> bool:
        """CSRF: cocokkan token csrf sesi dgn yg dikirim (only valid utk sesi aktif)."""
        if not token or not provided:
            return False
        rec = self._sessions.get(token.strip())
        if not rec:
            return False
        expected = rec.get("csrf")
        return bool(expected) and hmac.compare_digest(expected, (provided or "").strip())

    def active_count(self) -> int:
        return len(self._sessions)
