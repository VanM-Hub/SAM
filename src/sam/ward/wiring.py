"""ward/wiring.py — composition root Ward (W1).

Merakit komponen Ward yang SUDAH ADA menjadi satu composition root canonical
(Van #5 W1). Menyediakan:
  - `build_ward_manager()`  -> WardManager dgn WardRepository + persistence
                              (PostgreSQL bila dikonfigurasi, else InMemory).
  - `get_ward_manager()`    -> accessor singleton-lite (memakai ulang instance
                              composition root di proses yang sama).

TIDAK membuat execution pipeline kedua; WardManager hanya repo + boundary +
resolve/gate. Execution tetap via runner -> adapter -> existing runtime.

Persistence: mengikuti `build_ward_store` (PostgresWardStore / InMemory).
WardRepository menerima store via constructor (`persistence=`). Bila store
PG, __init__ memuat ulang state tersimpan (survive restart, accept E/F).
"""
from __future__ import annotations

from typing import Optional

from sam.ward.manager import WardManager
from sam.ward.persistence import build_ward_store
from sam.ward.registry.registry import WardRepository


class _WardCompositionRoot:
    """Singleton-lite composition root Ward (per proses).

    `manager` di-build sekaligus (WardManager + repo + persistence). Caller
    biasa memakai `get_ward_manager()`; test bisa mengganti via
    `set_ward_manager()` untuk inject fake/persistence terisolasi.
    """

    _instance: Optional[WardManager] = None
    _info: dict = {}

    @classmethod
    def build(cls, *, persist: Optional[bool] = None, tenant=None) -> WardManager:
        store, info = build_ward_store(persist=persist)
        repo = WardRepository(persistence=store)
        manager = WardManager(repository=repo, tenant=tenant)
        # W1: bootstrap Ward Lab pertama (OpenClaw) — eksplisit + idempotent.
        # Mendaftarkan OpenClaw sbg Ward + entrustment read-only sehingga
        # ter-resolve sbg Ward di server nyata (accept B/C W1).
        try:
            from sam.ward.bootstrap import bootstrap_openclaw_ward
            owner = ((tenant or {}).get("username") or "van")
            bootstrap_openclaw_ward(manager, owner_username=owner)
        except Exception:  # noqa: BLE001 - bootstrap tak boleh mematikan root
            pass
        cls._instance = manager
        cls._info = info
        return manager

    @classmethod
    def get(cls) -> WardManager:
        if cls._instance is None:
            cls.build()
        return cls._instance

    @classmethod
    def set(cls, manager: WardManager) -> None:
        cls._instance = manager

    @classmethod
    def info(cls) -> dict:
        return dict(cls._info)

    @classmethod
    def reset(cls) -> None:
        cls._instance = None
        cls._info = {}


def build_ward_manager(*, persist: Optional[bool] = None, tenant=None) -> WardManager:
    """Build composition root Ward (repo + persistence + manager)."""
    return _WardCompositionRoot.build(persist=persist, tenant=tenant)


def get_ward_manager() -> WardManager:
    """Accessor composition root Ward (membangun bila belum ada)."""
    return _WardCompositionRoot.get()


def set_ward_manager(manager: WardManager) -> None:
    """Set composition root Ward (test/inject)."""
    _WardCompositionRoot.set(manager)


def ward_persistence_info() -> dict:
    """Info backend persistence Ward (utk observability/audit, tanpa secret)."""
    return _WardCompositionRoot.info()


def reset_ward_manager() -> None:
    """Reset composition root (test isolation)."""
    _WardCompositionRoot.reset()
