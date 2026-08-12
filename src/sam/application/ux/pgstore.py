"""pgstore.py — MissionStore berbasis PostgreSQL (M11-002, fondasi persistent).

Plugin-opsional: menggantikan MissionStore JSON ATOM di `store.py` TANPA
menghapusnya. API Identik (`load / save / enable / clear`), sehingga
`MissionUXService` TIDAK berubah. Aktif hanya bila caller memberikan
`PostgresMissionStore(...)` eksplisit — default sistem tetap `MissionStore`
(JSON atomik) supaya environment dev/test yang sudah terbukti tidak berubah.

Konten yang disimpan TIDAK pernah memuat secret (payload sudah di-scrub oleh
UxMissionState.as_dict() + sanitized audit — sama seperti store.py).

Catatan jujur: ini FONDASI persistent storage M11-002. Belum berarti seluruh
transaksi SAM pindah ke postgres; hanya state mission yang dipersist ke
postgres bila backend ini dipilih. JSON tetap valid sebagai lintasan lokal.
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

import psycopg2
import psycopg2.pool

# Tabel tunggal penyimpanan state mission (key = "mission_state", value = JSON).
_SCHEMA = """
CREATE TABLE IF NOT EXISTS mission_store (
    key        TEXT PRIMARY KEY,
    payload    JSONB NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
"""

_GET = "SELECT payload FROM mission_store WHERE key = %s"
_SET = """
INSERT INTO mission_store (key, payload, updated_at)
VALUES (%s, %s::jsonb, now())
ON CONFLICT (key) DO UPDATE
    SET payload = EXCLUDED.payload, updated_at = now()
"""
_DEL = "DELETE FROM mission_store WHERE key = %s"


def _default_dsn() -> str:
    """DSN default produksi M11; boleh ditimpa argumen/env."""
    pw = os.environ.get("SAM_PG_PASSWORD", "")
    return (
        f"host={os.environ.get('SAM_PG_HOST', '127.0.0.1')} "
        f"port={os.environ.get('SAM_PG_PORT', '5432')} "
        f"dbname={os.environ.get('SAM_PG_DB', 'sam')} "
        f"user={os.environ.get('SAM_PG_USER', 'sam')} "
        f"password={pw}"
    )


class PostgresMissionStore:
    """Persist state mission ke PostgreSQL (plugin-opsional, API = MissionStore).

    - load ()  -> dict state atau None bila belum ada.
    - save ()  -> tulis/snapshot payload (JSONB atomik via INSERT ... ON CONFLICT).
    - enable() -> otomatis aktif (postgres selalu siap); disediakan utk
                  keseragaman API dengan MissionStore (return self).
    - clear()  -> hapus key state (reset, mis. test).
    """

    def __init__(
        self,
        dsn: Optional[str] = None,
        key: str = "mission_state",
        table: str = "mission_store",
        autocommit: bool = True,
    ) -> None:
        # Default DSN diambil dari env / path dev; boleh di-override utk test.
        self._dsn = dsn or _default_dsn()
        self._key = key
        self._table = table
        self._autocommit = autocommit
        # Pastikan tabel ada (idempotent).
        self._init_table()

    # -- koneksi --------------------------------------------------------
    def _conn(self):
        conn = psycopg2.connect(self._dsn)
        conn.autocommit = self._autocommit
        return conn

    def _init_table(self) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SCHEMA)
        finally:
            conn.close()

    # -- API MissionStore ----------------------------------------------
    def enable(self) -> "PostgresMissionStore":
        return self

    @property
    def path(self):
        # Keseragaman API: MissionStore.path = Path file. Postgres tdk punya
        # path file; kembalikan DSN agar caller yg iseng baca path tetap aman.
        return self._dsn

    def load(self) -> Optional[Dict[str, Any]]:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_GET, (self._key,))
                row = cur.fetchone()
                if row is None:
                    return None
                payload = row[0]
                if isinstance(payload, str):
                    return json.loads(payload)
                return dict(payload)
        except Exception:
            return None
        finally:
            conn.close()

    def save(self, payload: Dict[str, Any]) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_SET, (self._key, json.dumps(payload, ensure_ascii=False)))
        finally:
            conn.close()

    def clear(self) -> None:
        conn = self._conn()
        try:
            with conn.cursor() as cur:
                cur.execute(_DEL, (self._key,))
        finally:
            conn.close()
