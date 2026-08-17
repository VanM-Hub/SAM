"""WardStore — persistence Ward (W1).

Keputusan Van (2026-08-17): persistence Ward pakai PostgreSQL via existing
Repository Pattern — JANGAN membuat JSON WardStore baru. Ikuti persistence
boundary existing (MissionStore -> PostgresMissionStore; PersistenceUnit di
application/ux/repositories.py).

Design:
  - `WardStore` Protocol: save(snapshot, scope) / load(scope) / clear(scope).
  - `PostgresWardStore`: satu tabel JSONB (sam_ward) tempat menyimpan
    snapshot state Ward (wards + entrustments). Menggunakan DSN yang sama dgn
    persistence existing (SAM_PG_DSN / SAM_ENV=production / env PG).
  - `InMemoryWardStore`: utk dev/test (regresi M13 aman tanpa PG).
  - Factory `build_ward_store(persist: bool)` memilih backend sesuai config,
    persis seperti `build_persistence_unit` (application/ux/persistence.py).

TIDAK menyimpan credential: snapshot hanya berisi identitas + metadata + scope
+ entrustment; secret (token) TIDAK pernah masuk (API/UI/log/evidence — accept
J). Boundary credential tetap di execution_runtime/credential_boundary.py.
"""
from __future__ import annotations

import os
from typing import Any, Dict, Optional

# psycopg2 opsional (sama seperti pgstore.py). Impor gagal -> backend tidak PG.
try:
    import psycopg2  # noqa: F401
    _PG_OK = True
except Exception:  # pragma: no cover - psycopg2 tidak terpasang
    _PG_OK = False


_SCHEMA = """
CREATE TABLE IF NOT EXISTS sam_ward (
    scope_key   TEXT PRIMARY KEY,
    payload     JSONB NOT NULL,
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_GET = "SELECT payload FROM sam_ward WHERE scope_key = %s"
_SET = """
INSERT INTO sam_ward (scope_key, payload, updated_at)
VALUES (%s, %s::jsonb, now())
ON CONFLICT (scope_key) DO UPDATE
    SET payload = EXCLUDED.payload, updated_at = now()
"""
_DEL = "DELETE FROM sam_ward WHERE scope_key = %s"


def _default_dsn() -> str:
    """DSN default produksi — konsisten dgn pgstore/persistence existing."""
    pw = os.environ.get("SAM_PG_PASSWORD", "")
    return (
        f"host={os.environ.get('SAM_PG_HOST', '127.0.0.1')} "
        f"port={os.environ.get('SAM_PG_PORT', '5432')} "
        f"dbname={os.environ.get('SAM_PG_DB', 'sam')} "
        f"user={os.environ.get('SAM_PG_USER', 'sam')} "
        f"password={pw}"
    )


def is_postgres_available() -> bool:
    return _PG_OK


class PostgresWardStore:
    """Persist state Ward (wards + entrustments) ke PostgreSQL (W1, durable).

    API: save(snapshot, scope) / load(scope) / clear(scope).
    Mengikuti pola PostgresMissionStore (pgstore.py): koneksi per-call,
    JSONB atomik via INSERT ... ON CONFLICT.
    """

    def __init__(self, dsn: Optional[str] = None,
                 scope: str = "ward_default") -> None:
        self._dsn = dsn or _default_dsn()
        self._scope = scope
        self._init_table()

    def _conn(self):
        conn = psycopg2.connect(self._dsn)
        conn.autocommit = True
        return conn

    def _init_table(self) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA)
        finally:
            conn.close()

    def save(self, snapshot: Dict[str, Any], scope: str = "ward") -> None:
        import json
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SET, (scope, json.dumps(snapshot, ensure_ascii=False)))
        finally:
            conn.close()

    def load(self, scope: str = "ward") -> Optional[Dict[str, Any]]:
        import json
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_GET, (scope,))
                row = cur.fetchone()
                if row is None:
                    return None
                payload = row[0]
                if isinstance(payload, str):
                    return json.loads(payload)
                return dict(payload)
        except Exception:  # noqa: BLE001 - reload gagal -> None (repo kosong)
            return None
        finally:
            conn.close()

    def clear(self, scope: str = "ward") -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_DEL, (scope,))
        finally:
            conn.close()


class InMemoryWardStore:
    """Persist Ward dalam memori (dev/test; regresi M13 aman tanpa PG).

    Menjaga API sama dgn PostgresWardStore agar repository bisa swap.
    """

    def __init__(self) -> None:
        self._data: Dict[str, Dict[str, Any]] = {}

    def save(self, snapshot: Dict[str, Any], scope: str = "ward") -> None:
        self._data[scope] = snapshot

    def load(self, scope: str = "ward") -> Optional[Dict[str, Any]]:
        return self._data.get(scope)

    def clear(self, scope: str = "ward") -> None:
        self._data.pop(scope, None)


def build_ward_store(persist: Optional[bool] = None) -> Any:
    """Factory backend persistence Ward sesuai konfigurasi.

    - `persist=True` ATAU produksi (SAM_ENV=production) -> PostgresWardStore
      (WAJIB PG; bila tak tersedia -> InMemory + ditandai tidak siap).
    - `persist=None` default: PG bila SAM_PG_DSN / SAM_ENABLE_PG dikonfigurasi,
      selain itu InMemory (dev/test).
    - `persist=False` -> InMemory selalu.

    Returns (store, info): store instance + dict metadata {backend,
    production, ready, reason}. Mirip build_persistence_unit.
    """
    env = os.environ.get("SAM_ENV", "").strip()
    dsn_set = bool(os.environ.get("SAM_PG_DSN", "").strip()) or (
        os.environ.get("SAM_ENABLE_PG", "") == "1"
        and bool(os.environ.get("SAM_PG_PASSWORD", "").strip())
    )

    want_pg = persist if persist is not None else (dsn_set or env == "production")
    if not want_pg:
        return InMemoryWardStore(), {
            "backend": "in_memory", "production": False, "ready": True, "reason": ""}

    if not _PG_OK:
        return InMemoryWardStore(), {
            "backend": "none", "production": env == "production", "ready": False,
            "reason": "psycopg2 tidak tersedia (Ward tetap in-memory; produksi BLOCKED)"}

    try:
        store = PostgresWardStore()
    except Exception as exc:  # pragma: no cover
        return InMemoryWardStore(), {
            "backend": "none", "production": env == "production", "ready": False,
            "reason": f"Gagal inisialisasi PostgresWardStore: {exc}"}

    return store, {
        "backend": "postgres", "production": True, "ready": True, "reason": ""}
