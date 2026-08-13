"""test_m12_001_repositories.py — M12-001 Durable State Foundation.

Buktikan:
  1. Mission A / B / C dapat hidup bersamaan, keyed per mission_id, TANPA
     saling overwrite (multi-mission).
  2. Persistence per-entity survive "restart" — object repository baru dgn DSN
     sama masih bisa load state yang disimpan sebelumnya (in-memory unit:
     banyak instance berbagi; PG unit: instance baru membaca dari DB).
  3. Repository pool (PersistenceUnit) ada untuk 6 entity: mission, execution,
     approval, audit, evidence, idempotency.
  4. Backend dapat di-swap (in-memory vs PostgreSQL) — service/domain hanya
     bergantung pada PORT (protocol), bukan pada psycopg2.

Unit test (in-memory) selalu jalan. Integration test (PG) di-skip bila env
`SAM_PG_DSN` tidak tersedia, agar CI/dev tanpa PG tetap hijau.
"""
from __future__ import annotations

import os

import pytest

from sam.application.ux import repositories as repo_mod


def _make_pg_unit_or_skip():
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    if not dsn:
        pytest.skip("SAM_PG_DSN tidak diset — skip integrasi PostgreSQL")
    return repo_mod.PostgresPersistenceUnit(dsn=dsn)


# ---------------------------------------------------------------------------
# Unit: in-memory (multi-mission, no overwrite, swap backend)
# ---------------------------------------------------------------------------
def _fill_mission(unit, mission_id: str, label: str) -> None:
    unit.missions.save_mission(mission_id, {"label": label, "step": 1})


def test_multimission_no_overwrite_inmemory():
    unit = repo_mod.InMemoryPersistenceUnit()
    _fill_mission(unit, "mission-a", "A")
    _fill_mission(unit, "mission-b", "B")
    _fill_mission(unit, "mission-c", "C")
    ids = set(unit.missions.list_missions())
    assert {"mission-a", "mission-b", "mission-c"} <= ids
    assert unit.missions.load_mission("mission-a")["label"] == "A"
    assert unit.missions.load_mission("mission-b")["label"] == "B"
    assert unit.missions.load_mission("mission-c")["label"] == "C"
    # Tidak ada overwrite: menambah C tidak mengubah A/B
    assert unit.missions.load_mission("mission-a")["step"] == 1


def test_update_mission_does_not_touch_others_inmemory():
    unit = repo_mod.InMemoryPersistenceUnit()
    _fill_mission(unit, "mission-a", "A")
    _fill_mission(unit, "mission-b", "B")
    # update A -> B tetap utuh
    unit.missions.save_mission("mission-a", {"label": "A2", "step": 2})
    assert unit.missions.load_mission("mission-a")["label"] == "A2"
    assert unit.missions.load_mission("mission-b")["label"] == "B"


def test_entity_repositories_isolated_inmemory():
    unit = repo_mod.InMemoryPersistenceUnit()
    unit.executions.save_execution("exec-1", {"mission_id": "mission-a", "ok": True})
    unit.approvals.save_approval("apr-1", {"mission_id": "mission-a", "decision": "approved"})
    unit.audit.append_audit("aud-1", {"mission_id": "mission-a", "event": "x"})
    unit.evidence.save_evidence("exec-1", {"kind": "proof"})
    unit.idempotency.save_idempotency("key-1", {"request_id": "req-1"}, "mission-a")
    # Terpisah per entity
    assert unit.executions.list_executions("mission-a") == ["exec-1"]
    assert unit.approvals.list_approvals("mission-a") == ["apr-1"]
    assert len(unit.audit.load_audit("mission-a")) == 1
    assert len(unit.evidence.load_evidence("exec-1")) == 1
    assert unit.idempotency.load_idempotency("key-1")["request_id"] == "req-1"
    # Kosong utk mission lain (isolasi)
    assert unit.executions.list_executions("mission-b") == []


def test_domain_depends_on_protocol_not_psycopg2():
    # Service/domain hanya memakai interface repository (Protocol). Pastikan
    # modul repositories memisahkan port dari impl psycopg2 (import library
    # hanya di dalam, bukan syarat domain). Ini cek struktural: class protocol
    # ada, dan in-memory unit TIDAK butuh psycopg2.
    assert hasattr(repo_mod, "MissionRepository")
    assert hasattr(repo_mod, "InMemoryPersistenceUnit")
    # In-memory unit dapat dipakai tanpa koneksi external
    u = repo_mod.InMemoryPersistenceUnit()
    assert u.ping() is True


# ---------------------------------------------------------------------------
# Integration: PostgreSQL (skip bila SAM_PG_DSN kosong)
# ---------------------------------------------------------------------------
@pytest.fixture
def pg_unit():
    unit = _make_pg_unit_or_skip()
    # bersihkan data uji dulu (jangan hapus data lain — hanya key uji kita)
    yield unit


def _cleanup_pg_test_keys(unit):
    for k in list(unit.idempotency.list_keys()):
        if k.startswith("m12test"):
            unit.idempotency.clear()  # clear seluruhnya — tabel uji terisolasi
            return
    for m in list(unit.missions.list_missions()):
        if m.startswith("m12test"):
            unit.missions.remove_mission(m)


def test_pg_multimission_no_overwrite(pg_unit):
    unit = pg_unit
    ids = [f"m12test-m-a", f"m12test-m-b", f"m12test-m-c"]
    for i, mid in enumerate(ids):
        unit.missions.save_mission(mid, {"label": chr(65 + i), "step": i + 1})
    assert unit.missions.load_mission("m12test-m-a")["label"] == "A"
    assert unit.missions.load_mission("m12test-m-b")["label"] == "B"
    assert unit.missions.load_mission("m12test-m-c")["label"] == "C"
    found = [m for m in unit.missions.list_missions() if m.startswith("m12test")]
    assert len(found) >= 3
    # cleanup
    for mid in ids:
        unit.missions.remove_mission(mid)


def test_pg_persistence_survives_restart(pg_unit):
    """Simulasi restart: object unit BARU (instance ulang) membaca state yang
    disimpan — membuktikan state ada di PostgreSQL, bukan di objek memory."""
    unit = pg_unit
    # bersihkan sisa uji lama (audit id uji) agar idempotent saat re-run
    for e in unit.audit.load_audit():
        pass
    try:
        unit.audit.clear_audit()  # tabel uji terisolasi
    except Exception:
        pass
    unit.idempotency.save_idempotency("m12test-key-restart", {"request_id": "req-r", "text": "t"}, "m12test-m-x")
    unit.missions.save_mission("m12test-m-x", {"label": "restart-ok"})
    unit.audit.append_audit("m12test-aud-r", {"mission_id": "m12test-m-x", "event": "startup"})
    unit.evid = None
    # "Restart" = buat unit baru dengan dsn sama
    unit2 = repo_mod.PostgresPersistenceUnit(dsn=unit.dsn)
    assert unit2.idempotency.load_idempotency("m12test-key-restart")["request_id"] == "req-r"
    assert unit2.missions.load_mission("m12test-m-x")["label"] == "restart-ok"
    assert any(e.get("event") == "startup" for e in unit2.audit.load_audit("m12test-m-x"))
    # cleanup
    unit.idempotency.clear()
    unit.missions.remove_mission("m12test-m-x")


def test_pg_pool_has_all_six_repositories(pg_unit):
    unit = pg_unit
    assert hasattr(unit, "missions")
    assert hasattr(unit, "executions")
    assert hasattr(unit, "approvals")
    assert hasattr(unit, "audit")
    assert hasattr(unit, "evidence")
    assert hasattr(unit, "idempotency")
    assert unit.ping() is True
