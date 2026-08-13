"""test_m12_004_005_fail_closed.py — M12-004 Production Persistence Activation
& M12-005 Fail-Closed Persistence (P0).

M12-004: produksi (SAM_ENV=production) WAJIB PostgreSQL. Tanpa DSN atau PG
         down -> TIDAK memilih in-memory; ditandai not-ready.
M12-005: saat produksi tidak siap, operasi mission (submit/decide) DI-BLOCK
         (0 mission baru, 0 mutation) — tanpa fallback diam-diam ke in-memory.

Default dev (tanpa SAM_ENV) tetap memakai perilaku lama (in-memory/JSON) —
regresi M10 aman.
"""
from __future__ import annotations

import os

import pytest

from sam.application.ux import persistence, repositories
from sam.application.ux.service import MissionUXService


@pytest.fixture(autouse=True)
def _clean_env():
    saved = {
        k: os.environ.get(k) for k in ("SAM_ENV", "SAM_PG_DSN", "SAM_ENABLE_PG", "SAM_PG_PASSWORD")
    }
    yield
    for k, v in saved.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v


def _pg_dsn():
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    if not dsn:
        pytest.skip("SAM_PG_DSN tidak diset — skip integrasi PostgreSQL")
    return dsn


def test_production_requires_pg_not_inmemory(monkeypatch):
    """M12-004: SAM_ENV=production tanpa DSN -> ready=False, backend bukan umpan
    diam-diam ke in-memory."""
    monkeypatch.setenv("SAM_ENV", "production")
    monkeypatch.delenv("SAM_PG_DSN", raising=False)
    _unit, info = persistence.build_persistence_unit()
    assert info["production"] is True
    assert info["ready"] is False
    assert info["backend"] in ("none",)
    assert "SAM_PG_DSN" in info.get("reason", "")


def test_production_with_pg_ready(monkeypatch):
    """M12-004: produksi + DSN valid -> PostgreSQL, ready."""
    monkeypatch.setenv("SAM_ENV", "production")
    monkeypatch.setenv("SAM_PG_DSN", _pg_dsn())
    _unit, info = persistence.build_persistence_unit()
    assert info["production"] is True
    assert info["backend"] == "postgres"
    assert info["ready"] is True
    assert isinstance(_unit, repositories.PostgresPersistenceUnit)


def test_production_pg_down_fail_closed(monkeypatch):
    """M12-004/005: produksi + DSN ke PG yang mati -> ready=False (fail-closed)."""
    monkeypatch.setenv("SAM_ENV", "production")
    monkeypatch.setenv("SAM_PG_DSN", "host=127.0.0.1 port=1 dbname=sam user=sam password=x")
    _unit, info = persistence.build_persistence_unit()
    assert info["production"] is True
    assert info["ready"] is False


def test_service_blocks_submit_when_production_down(monkeypatch):
    """M12-005: produksi tidak siap -> submit DI-BLOCK, 0 mission tersimpan."""
    monkeypatch.setenv("SAM_ENV", "production")
    monkeypatch.setenv("SAM_PG_DSN", "host=127.0.0.1 port=1 dbname=sam user=sam password=x")
    svc = MissionUXService()
    assert svc._production_blocked is True
    st = svc.submit("buat issue github judul: M12 block", idempotency_key="m12block-key")
    assert st.status == "blocked"
    assert st.failure_kind == "persistence-required"
    # tidak ada mission tersimpan ke repositori manapun (persistence None)
    assert svc._persistence is None
    # tidak ada idempotency baru terekam (operasi ditolak)
    assert "m12block-key" not in svc._idem


def test_service_blocks_decide_when_production_down(monkeypatch):
    """M12-005: produksi tidak siap -> decide (approve) DI-BLOCK, 0 mutation."""
    monkeypatch.setenv("SAM_ENV", "production")
    monkeypatch.setenv("SAM_PG_DSN", "host=127.0.0.1 port=1 dbname=sam user=sam password=x")
    from sam.application.ux.approval import ApprovalDecisionIntent
    svc = MissionUXService()
    assert svc._production_blocked is True
    st = svc.decide(ApprovalDecisionIntent.APPROVE, approver="van")
    assert st.status == "blocked"


def test_dev_default_not_blocked(monkeypatch):
    """M12-004: dev (tanpa SAM_ENV) TIDAK fail-closed — perilaku lama tetap."""
    monkeypatch.delenv("SAM_ENV", raising=False)
    monkeypatch.setenv("SAM_PG_DSN", _pg_dsn())
    _unit, info = persistence.build_persistence_unit()
    assert info["ready"] is True
    assert info["production"] is True  # DSN diset -> PG; tapi bukan fail-closed wajib
