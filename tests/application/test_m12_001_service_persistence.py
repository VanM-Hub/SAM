"""test_m12_001_service_persistence.py — M12-001: wiring service ke repository.

Buktikan di level APLIKASI bahwa MissionUXService:
  1. Saat diberi PersistenceUnit PostgreSQL, setiap mutasi (submit / recover)
     memakai repository per-entity sebagai source of truth.
  2. Simulasi restart (instance service BARU dengan unit yang sama / DSN sama)
     memulihkan mission yang sudah tersimpan (survive restart, truth tidak hilang).
  3. Tanpa PersistenceUnit, perilaku tidak berubah (regresi M10 aman).

`_interpret` di-monkeypatch agar deterministik & cepat (tanpa panggilan AI).
Integrasi PG di-skip bila SAM_PG_DSN tidak tersedia.
"""
from __future__ import annotations

import os

import pytest

from sam.application.ux.service import MissionUXService


def _fake_interpret_github(text):
    # Deterministik: "github issue" -> operasi github.create_issue
    return (
        "github.create_issue",
        "VanM-Hub/test-issues",
        "SAM memahami: membuat GitHub issue (test wiring M12-001).",
        ["verifikasi koneksi", "membuat issue", "verifikasi independen"],
        "SAM akan membuat GitHub issue di repo VanM-Hub/test-issues.",
        "Persetujuan diperlukan sebelum eksekusi.",
    )


def _make_pg_unit_or_skip():
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    if not dsn:
        pytest.skip("SAM_PG_DSN tidak diset — skip integrasi PostgreSQL")
    from sam.application.ux import repositories
    return repositories.PostgresPersistenceUnit(dsn=dsn)


@pytest.fixture
def pg_unit():
    return _make_pg_unit_or_skip()


def _cleanup(unit, prefix):
    for m in list(unit.missions.list_missions()):
        if m.startswith(prefix):
            unit.missions.remove_mission(m)
    for k in list(unit.idempotency.list_keys()):
        if k.startswith(prefix):
            unit.idempotency.clear()  # tabel uji terisolasi
            return


def test_service_persists_mission_to_repository(pg_unit, monkeypatch):
    monkeypatch.setattr(MissionUXService, "_interpret", staticmethod(_fake_interpret_github))
    unit = pg_unit
    _cleanup(unit, "m12srv")
    svc = MissionUXService(persistence=unit)
    st = svc.submit("buat issue github judul: M12 wiring test", idempotency_key="m12srv-key-1")
    mission_id = (st.observability or {}).get("mission_id")
    assert mission_id
    # Misi tersimpan di repository PG
    stored = unit.missions.load_mission(mission_id)
    assert stored is not None
    assert stored.get("request") == "buat issue github judul: M12 wiring test"
    # cleanup
    _cleanup(unit, "m12srv")


def test_service_recovers_mission_after_restart(pg_unit, monkeypatch):
    """Simulasi restart: service BARU (unit/DSN sama) memulihkan mission yang
    sudah disimpan — membuktikan truth tidak hilang saat process restart."""
    monkeypatch.setattr(MissionUXService, "_interpret", staticmethod(_fake_interpret_github))
    unit = pg_unit
    _cleanup(unit, "m12srv")
    # service v1: submit -> state tersimpan di PG
    svc1 = MissionUXService(persistence=unit)
    st1 = svc1.submit("buat issue github judul: restart test", idempotency_key="m12srv-key-r")
    mission_id = (st1.observability or {}).get("mission_id")
    assert mission_id
    # service v2 (restart): unit BARU dengan DSN sama -> recover dari PG
    from sam.application.ux import repositories
    unit2 = repositories.PostgresPersistenceUnit(dsn=unit.dsn)
    svc2 = MissionUXService(persistence=unit2)
    recovered = svc2.get_state()
    assert recovered is not None, "state harus dipulihkan setelah restart"
    assert (recovered.observability or {}).get("mission_id") == mission_id
    assert recovered.request_id == st1.request_id
    # cleanup
    _cleanup(unit, "m12srv")


def test_service_default_backend_unchanged(monkeypatch):
    """Tanpa PersistenceUnit & tanpa env PG, service tidak mengaktifkan repo
    (regresi M10: in-memory / JSON)."""
    monkeypatch.setattr(MissionUXService, "_interpret", staticmethod(_fake_interpret_github))
    # pastikan env PG tidak diset
    prev = os.environ.pop("SAM_PG_DSN", None)
    try:
        svc = MissionUXService()
        assert svc._persistence is None
    finally:
        if prev is not None:
            os.environ["SAM_PG_DSN"] = prev
