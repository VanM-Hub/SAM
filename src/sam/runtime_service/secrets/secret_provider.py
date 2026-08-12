"""SecretProvider (Sprint 263).

Program D - Runtime Services & Deployment.
Mengambil secret hanya dari environment. Tidak pernah hardcode.
"""
from __future__ import annotations
import os
from typing import Dict, Optional


class SecretProvider:
    """Penyedia secret dari environment (sync, deterministic)."""

    def __init__(self, env: Optional[Dict[str, str]] = None) -> None:
        self._env = env if env is not None else os.environ

    def get(self, key: str) -> Optional[str]:
        """Ambil secret dari env. Return None jika tidak ada."""
        return self._env.get(key)

    def has(self, key: str) -> bool:
        return key in self._env

    def resolve_all(self, keys: list) -> Dict[str, str]:
        """Ambil sekumpulan secret yang tersedia."""
        return {k: self._env[k] for k in keys if k in self._env}

    def required(self, key: str) -> str:
        value = self._env.get(key)
        if not value:
            raise KeyError(f"required secret missing from env: {key}")
        return value


# env untuk mengaktifkan secret store PostgreSQL (M11-003), opt-in
PG_SECRETS_ENABLE_ENV = "SAM_ENABLE_PG_SECRETS"


def default_secret_provider() -> "SecretProvider":
    """Pabrik SecretProvider default.

    Bila env `SAM_ENABLE_PG_SECRETS` bernilai 1, memakai PgSecretProvider
    (PostgreSQL terenkripsi, M11-003). Bila tidak, memakai SecretProvider
    (env-only, perilaku default yang sudah terbukti M8/M10).

    Import PgSecretProvider dilakukan lazy (di dalam fungsi) agar modul ini
    tetap bisa diimpor tanpa dependensi psycopg2/cryptography bila PG tidak
    dipakai (offline / regresi ringan).
    """
    import os
    if os.environ.get(PG_SECRETS_ENABLE_ENV) == "1":
        from sam.runtime_service.secrets.pg_secret_provider import PgSecretProvider
        return PgSecretProvider()
    return SecretProvider()
