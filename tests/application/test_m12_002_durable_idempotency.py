"""test_m12_002_durable_idempotency.py — M12-002 Durable Idempotency (P0).

Buktikan:
  1. `self._idem` TIDAK lagi satu-satunya source idempotency — saat PersistenceUnit
     ada, idempotency key disimpan di IdempotencyRepository (survive restart).
  2. Restart-retry: submit(key sama) SETELAH restart TIDAK membuat mission baru
     dan TIDAK menimbulkan execution/mutation kedua (dedupe lintas process).
  3. Deterministik: same key + same text -> state sama; jumlah mission utk key
     tsb tetap 1 (bukan 2).
  4. Same key + text berbeda -> dianggap operasi baru (tidak disalah-dedup).

Integrasi PG di-skip bila SAM_PG_DSN tidak tersedia; unit in-memory selalu jalan.
"""
from __future__ import annotations

import os

import pytest

from sam.application.ux.service import MissionUXService
from sam.application.ux import repositories


def _fake_interpret_github(text):
    return (
        "github.create_issue",
        "VanM-Hub/test-issues",
        "SAM memahami: membuat GitHub issue (test M12-002).",
        ["verifikasi koneksi", "membuat issue", "verifikasi independen"],
        "SAM akan membuat GitHub issue di repo VanM-Hub/test-issues.",
        "Persetujuan diperlukan sebelum eksekusi.",
    )


def _unit():
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    if dsn:
        return repositories.PostgresPersistenceUnit(dsn=dsn)
    return repositories.InMemoryPersistenceUnit()


def _cleanup(unit):
    # Hapus mission uji (request text dimulai "buat issue github judul") + idempotency uji.
    try:
        for m in list(unit.missions.list_missions()):
            data = unit.missions.load_mission(m)
            if data and (data.get("request") or "").startswith("buat issue github judul"):
                unit.missions.remove_mission(m)
    except Exception:
        pass
    try:
        unit.idempotency.clear()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _fresh_unit():
    u = _unit()
    _cleanup(u)
    yield u
    _cleanup(u)


def _missions_for_text(unit, text):
    """Misi yang request text-nya sama dengan text (load isi per mission)."""
    out = []
    try:
        for mid in unit.missions.list_missions():
            data = unit.missions.load_mission(mid)
            if data and data.get("request") == text:
                out.append(mid)
    except Exception:
        pass
    return out


THE_TEXT = "buat issue github judul: M12 idem dedup"


def test_retry_same_key_after_restart_no_duplicate(monkeypatch):
    """Inti acceptance M12-002: request A -> (restart) -> retry key A.
    Mission baru TIDAK dibuat kedua kali; state yang dikembalikan sama."""
    monkeypatch.setattr(MissionUXService, "_interpret", staticmethod(_fake_interpret_github))
    unit = _unit()
    # Run 1 (process 1)
    svc1 = MissionUXService(persistence=unit)
    st1 = svc1.submit(THE_TEXT, idempotency_key="m12idem-key-A")
    assert (st1.observability or {}).get("mission_id")
    assert len(_missions_for_text(unit, THE_TEXT)) == 1
    # Simulasi restart: service BARU + unit/DSN sama
    svc2 = MissionUXService(persistence=unit)
    st2 = svc2.submit(THE_TEXT, idempotency_key="m12idem-key-A")
    # state yang dikembalikan = mission yang sama (bukan mission baru)
    assert (st2.observability or {}).get("mission_id") == (st1.observability or {}).get("mission_id")
    # TIDAK ada mission duplikat utk text ini
    assert len(_missions_for_text(unit, THE_TEXT)) == 1


def test_same_key_different_text_new_operation(monkeypatch):
    """Key sama tapi text beda -> dianggap operasi baru (bukan salah dedup)."""
    monkeypatch.setattr(MissionUXService, "_interpret", staticmethod(_fake_interpret_github))
    unit = _unit()
    svc = MissionUXService(persistence=unit)
    svc.submit(THE_TEXT, idempotency_key="m12idem-key-B")
    # text beda dengan key sama -> mission baru (tidak di-dedup)
    svc.submit("buat issue github judul: berbeda", idempotency_key="m12idem-key-B")
    assert len(_missions_for_text(unit, THE_TEXT)) == 1
    assert len(_missions_for_text(unit, "buat issue github judul: berbeda")) == 1
    assert len(_missions_for_text(unit, THE_TEXT)) + len(
        _missions_for_text(unit, "buat issue github judul: berbeda")) == 2


def test_idempotency_repo_populated_after_submit(monkeypatch):
    """Setelah submit, key tersimpan di idempotency repository (durable)."""
    monkeypatch.setattr(MissionUXService, "_interpret", staticmethod(_fake_interpret_github))
    unit = _unit()
    svc = MissionUXService(persistence=unit)
    svc.submit(THE_TEXT, idempotency_key="m12idem-key-C")
    rec = unit.idempotency.load_idempotency("m12idem-key-C")
    assert rec is not None
    assert rec.get("text") == THE_TEXT
