"""PgSecretProvider (M11-003 Production Secrets).

Secret manager terpusat berbasis PostgreSQL TERENKRIPSI (Fernet/AES-GCM).

Aliran credential (jalur tunggal, reuse pola yang sudah PROVEN):

    SecretStore (PostgreSQL, ciphertext) -> SecretProvider -> CredentialBoundary -> Connector

Perbedaan dengan SecretProvider (env-only):
  - Nilai secret disimpan TERENKRIPSI di tabel `secret_store` di PostgreSQL
    (bukan teks polos di env/file teks).
  - Master key untuk enkripsi TIDAK di DB (baca dari file di luar project,
    default `~/.sam/master.key` atau env `SAM_MASTER_KEY_FILE`).
  - Fallback: bila key tidak ada di store, get() meneruskan ke env
    (kompatibilitas / migrasi bertahap / offline).
  - Bila PostgreSQL tidak tersedia, provider berperilaku seperti env biasa
    (TIDAK memutuskan jalur yang sudah terbukti).

Kontrak sama persis dengan SecretProvider (get/has/resolve_all/required),
sehingga bisa di-pass langsung ke CredentialBoundary(provider=...).
"""
from __future__ import annotations

import datetime as _dt
import os
from typing import Dict, Optional

from cryptography.fernet import Fernet, InvalidToken

from sam.runtime_service.secrets.secret_provider import SecretProvider

# env yang menimpa PATH file master key (default di luar project)
MASTER_KEY_FILE_ENV = "SAM_MASTER_KEY_FILE"

# default path master key: di luar project & di luar repo
_DEFAULT_MASTER_KEY = os.path.join(
    os.path.expanduser("~"), ".sam", "master.key"
)

# env untuk DSN PostgreSQL secret store (default memakai db `sam` lokal)
PG_DSN_ENV = "SAM_PG_DSN"
_PG_DEFAULT_DSN = "host=127.0.0.1 port=5432 dbname=sam user=sam"

# env mode produksi (fail-closed secret enforcement)
PRODUCTION_ENV = "SAM_ENV"
PRODUCTION_VALUE = "production"


class SecretUnavailableError(RuntimeError):
    """Secret tidak dapat diperoleh dalam mode ketat (produksi).

    Dipakai untuk fail-closed: bila secret store wajib tapi tidak bisa
    dipakai / master key hilang / decrypt gagal / key tak ada -> BLOCKED,
    bukan fallback diam-diam ke env.
    """


class InternalSecretAudit:
    """Audit minimal akses secret (masked saja, tanpa raw)."""

    def __init__(self) -> None:
        self.records: list = []

    def append(self, key: str, action: str, result: str) -> None:
        if hasattr(_dt, "timezone"):
            now = _dt.datetime.now(_dt.timezone.utc).isoformat()
        else:
            now = _dt.datetime.utcnow().isoformat()
        self.records.append({
            "key": key,
            "action": action,
            "result": result,
            "at": now,
        })

    def as_dict(self) -> Dict:
        return {"access": self.records}


class PgSecretProvider(SecretProvider):
    """Secret provider PostgreSQL terenkripsi (fallback ke env bila perlu).

    Contructor opsional untuk determinisme test:
      - dsn: DSN psycopg2 (default dari env SAM_PG_DSN / default lokal)
      - env: mapping env (untuk test; default os.environ)
      - master_key_path: path file master key (default ke MASTER_KEY_FILE)
      - allow_auto_key: auto-generate master key bila file belum ada (default True)
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        env: Optional[Dict[str, str]] = None,
        master_key_path: Optional[str] = None,
        allow_auto_key: bool = True,
        strict: Optional[bool] = None,
    ) -> None:
        super().__init__(env=env)
        self._env = env if env is not None else os.environ
        self._dsn = dsn or self._env.get(PG_DSN_ENV) or _PG_DEFAULT_DSN
        self._master_key_path = (
            master_key_path
            or self._env.get(MASTER_KEY_FILE_ENV)
            or _DEFAULT_MASTER_KEY
        )
        # strict: bila None, deteksi dari SAM_ENV=production (fail-closed)
        if strict is None:
            strict = self._env.get(PRODUCTION_ENV) == PRODUCTION_VALUE
        self._strict = bool(strict)
        self._allow_auto_key = bool(allow_auto_key)
        self._fernet: Optional[Fernet] = None
        self._audit = InternalSecretAudit()

    def is_strict(self) -> bool:
        """True bila mode ketat (produksi) sedang aktif."""
        return self._strict

    def _load_or_create_key(self) -> bytes:
        """Load master key dari file.

        strict=True: file Wajib ada -> bila hilang RAISE SecretUnavailableError
        (BLOCKED, bukan auto-gen). dev (strict=False): auto-generate bila belum
        ada (perilaku lama).
        """
        path = os.path.expanduser(self._master_key_path)
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                raw = fh.read().strip()
            if raw:
                return raw.encode("utf-8")
            if self._strict:
                raise SecretUnavailableError(
                    f"master key file kosong (BLOCKED, produksi): {path}"
                )
        if self._strict:
            raise SecretUnavailableError(
                f"master key file tidak ada (BLOCKED, produksi): {path}"
            )
        if not self._allow_auto_key:
            raise SecretUnavailableError(
                f"master key file tidak ada & auto-gen dimatikan: {path}"
            )
        # generate key baru (Fernet key berbasis urlsafe base64, 32 byte)
        key = Fernet.generate_key()
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(key.decode("utf-8") + "\n")
        return key

    def _fernet_instance(self) -> Fernet:
        if self._fernet is None:
            self._fernet = Fernet(self._load_or_create_key())
        return self._fernet

    def _encrypt(self, plaintext: str) -> str:
        return self._fernet_instance().encrypt(plaintext.encode("utf-8")).decode("utf-8")

    def _decrypt(self, ciphertext: str) -> str:
        return self._fernet_instance().decrypt(ciphertext.encode("utf-8")).decode("utf-8")

    # --- akses PostgreSQL (lazy; blokir bila tidak tersedia) ---
    def _psql_available(self) -> bool:
        try:
            import psycopg2  # noqa: F401
            return True
        except Exception:
            return False

    def _connect(self):
        import psycopg2
        return psycopg2.connect(self._dsn)

    def _ensure_table(self, conn) -> None:
        with conn.cursor() as cur:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS secret_store (
                    key         TEXT PRIMARY KEY,
                    ciphertext  TEXT NOT NULL,
                    created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
                    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
                )
                """
            )
        conn.commit()

    def _store_get(self, key: str) -> Optional[str]:
        """Ambil ciphertext dari store. None bila key tidak ada / PG tidak ada."""
        if not self._psql_available():
            return None
        try:
            conn = self._connect()
            try:
                self._ensure_table(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT ciphertext FROM secret_store WHERE key = %s",
                        (key,),
                    )
                    row = cur.fetchone()
                return row[0] if row else None
            finally:
                conn.close()
        except Exception:
            # PG tidak tersedia -> jangan putus jalur; fallback ke env
            return None

    def _store_set(self, key: str, ciphertext: str) -> bool:
        if not self._psql_available():
            return False
        try:
            conn = self._connect()
            try:
                self._ensure_table(conn)
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        INSERT INTO secret_store (key, ciphertext, updated_at)
                        VALUES (%s, %s, now())
                        ON CONFLICT (key)
                        DO UPDATE SET ciphertext = EXCLUDED.ciphertext,
                                      updated_at = now()
                        """,
                        (key, ciphertext),
                    )
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception:
            return False

    # --- kontrak SecretProvider ---
    def get(self, key: str) -> Optional[str]:
        """Ambil secret: store (dekripsi) dulu.

        strict=True (produksi): store WAJIB. Bila store tidak tersedia /
        key tidak ada di store / decrypt gagal -> RAISE SecretUnavailableError
        (BLOCKED). TIDAK fallback ke env diam-diam.
        strict=False (dev): fallback ke env bila tak ada di store (perilaku lama).
        """
        stored = self._store_get(key)
        if stored is not None:
            try:
                value = self._decrypt(stored)
            except InvalidToken:
                self._audit.append(key, "get", "decrypt_failed")
                if self._strict:
                    raise SecretUnavailableError(
                        f"secret decrypt gagal (BLOCKED, produksi): {key}"
                    )
                return None
            self._audit.append(key, "get", "store")
            return value
        if self._strict:
            # store tak punya key ini -> fail-closed, jangan bocorkan env
            self._audit.append(key, "get", "blocked_missing")
            raise SecretUnavailableError(
                f"secret tidak ada di store (BLOCKED, produksi): {key}"
            )
        # dev: fallback env (kompatibilitas / migrasi bertahap)
        value = self._env.get(key)
        if value is not None:
            self._audit.append(key, "get", "env")
        else:
            self._audit.append(key, "get", "missing")
        return value

    def has(self, key: str) -> bool:
        if self._strict:
            # strict: "ada" berarti BISA dibaca dari store secara aman
            try:
                stored = self._store_get(key)
            except Exception:
                return False
            if stored is None:
                return False
            try:
                self._decrypt(stored)
                return True
            except InvalidToken:
                return False
        return self.get(key) is not None

    def resolve_all(self, keys: list) -> Dict[str, str]:
        out = {}
        for k in keys:
            v = self.get(k)  # strict akan raise bila tak tersedia
            if v is not None:
                out[k] = v
        return out

    def required(self, key: str) -> str:
        try:
            value = self.get(key)
        except SecretUnavailableError:
            raise
        if not value:
            raise KeyError(f"required secret missing: {key}")
        return value

    # --- API tambahan (seeding / admin) ---
    def set_secret(self, key: str, value: str) -> bool:
        """Simpan secret TERENKRIPSI ke store. True bila tersimpan di PG."""
        return self._store_set(key, self._encrypt(value))

    def delete_secret(self, key: str) -> bool:
        if not self._psql_available():
            return False
        try:
            conn = self._connect()
            try:
                self._ensure_table(conn)
                with conn.cursor() as cur:
                    cur.execute("DELETE FROM secret_store WHERE key = %s", (key,))
                conn.commit()
                return True
            finally:
                conn.close()
        except Exception:
            return False

    def list_secret_keys(self) -> list:
        """Daftar key di store (TANPA nilai; admin/sync ke UI secukupnya)."""
        if not self._psql_available():
            return []
        try:
            conn = self._connect()
            try:
                self._ensure_table(conn)
                with conn.cursor() as cur:
                    cur.execute("SELECT key FROM secret_store ORDER BY key")
                    return [r[0] for r in cur.fetchall()]
            finally:
                conn.close()
        except Exception:
            return []

    def audit(self) -> Dict:
        return self._audit.as_dict()
