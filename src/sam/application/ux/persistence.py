"""persistence.py — Factory PersistenceUnit untuk M12-001/004/005.

Memilih backend persistence berdasarkan konfigurasi:
  - `SAM_PG_DSN` diset (produksi)      -> PostgresPersistenceUnit (durable, fail-closed).
  - `SAM_ENABLE_PG=1` + DSN tersedia   -> PostgresPersistenceUnit.
  - default (dev/test)                 -> InMemoryPersistenceUnit (regresi M10 aman).

Factory ini menjaga DOMAIN (service) tetap bergantung pada interface
`PersistenceUnit`, bukan pada PostgreSQL. Backend dapat di-swap di satu titik.

M12-004 (Production Persistence Activation) ingin produksi = PostgreSQL
REQUIRED, dan PG down -> NOT READY (bukan silent fallback). Implementasi
fail-closed diselesaikan di M12-005; factory ini fokus memilih backend yang
benar dan menandai apakah produksi aktif.
"""
from __future__ import annotations

import os
from typing import Optional, Tuple

from sam.application.ux import repositories


def is_postgres_configured() -> bool:
    """True bila lingkungan dikonfigurasi untuk memakai PostgreSQL."""
    return bool(os.environ.get("SAM_PG_DSN", "").strip()) or (
        os.environ.get("SAM_ENABLE_PG", "") == "1"
        and bool(os.environ.get("SAM_PG_PASSWORD", "").strip())
    )


def build_persistence_unit(
    force: Optional[str] = None,
) -> Tuple[object, dict]:
    """Bangun PersistenceUnit sesuai konfigurasi.

    Returns (unit, info):
      unit : instance PersistenceUnit (PG atau in-memory)
      info : dict metadata {backend, production, ready, reason}

    M12-004/005 (Fail-Closed Production): bila `SAM_ENV=production`,
    PostgreSQL WAJIB tersedia & reachable. Tanpa DSN atau PG down ->
    `info[\"ready\"]=False` (TIDAK memilih in-memory; produksi TIDAK boleh
    diam-diam fallback). Pemanggil (service) harus mem-BLOCK operasi saat
    produksi belum siap. Dev/test (tanpa SAM_ENV) memakai perilaku lama."""
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    env = os.environ.get("SAM_ENV", "").strip()
    if force == "pg" or env == "production":
        if force == "pg":
            unit = repositories.PostgresPersistenceUnit(dsn=dsn or None)
            return unit, {"backend": "postgres", "production": True,
                          "ready": True, "reason": ""}
        # Produksi: WAJIB PG, fallback TIDAK diizinkan.
        if not dsn:
            return repositories.InMemoryPersistenceUnit(), {
                "backend": "none", "production": True, "ready": False,
                "reason": "SAM_ENV=production membutuhkan SAM_PG_DSN (PostgreSQL REQUIRED di produksi)"}
        try:
            unit = repositories.PostgresPersistenceUnit(dsn=dsn)
        except Exception as exc:  # pragma: no cover
            return repositories.InMemoryPersistenceUnit(), {
                "backend": "none", "production": True, "ready": False,
                "reason": f"Gagal inisialisasi PostgreSQL: {exc}"}
        try:
            ok = unit.ping()
        except Exception:  # pragma: no cover
            ok = False
        return unit, {"backend": "postgres", "production": True,
                      "ready": ok,
                      "reason": "" if ok else "PostgreSQL unreachable (fail-closed)"}
    if is_postgres_configured():
        unit = repositories.PostgresPersistenceUnit(dsn=dsn or None)
        return unit, {"backend": "postgres", "production": True,
                      "ready": True, "reason": ""}
    unit = repositories.InMemoryPersistenceUnit()
    return unit, {"backend": "in_memory", "production": False,
                  "ready": True, "reason": ""}
