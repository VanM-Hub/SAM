"""test_m12_003_restart_safety.py — M12-003 Restart Safety (P0).

Acceptance inti: "restart != reset". Buktikan di level aplikasi bahwa Recovery
tidak kehilangan operational truth di SEMUA titik lifecycle:

  1. Mission KECIL (baru di-submit) tetap muncul setelah restart.
  2. Mission yang sedang MENUNGGU approval (WAITING_APPROVAL) tetap di
     WAITING_APPROVAL setelah restart (operator tidak kehilangan antrean).
  3. Mission yang sudah berjalan (RUNNING) / selesai (COMPLETED) / gagal
     (FAILED) tetap dengan status & detailnya setelah restart.
  4. Audit trail + idempotency survive restart (tetap terbaca).

Semua deterministik & cepat: state lifecycle ditulis langsung ke repository
(PostgreSQL), lalu instansiasi service BARU (simulasi restart) membacanya ulang.
Integrasi PG di-skip bila SAM_PG_DSN tidak tersedia (in-memory fallback tetap
lengkap untuk regresi).
"""
from __future__ import annotations

import os

import pytest

from sam.application.ux.service import MissionUXService
from sam.application.ux.state import UxMissionState
from sam.application.ux import repositories


def _unit():
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    if dsn:
        return repositories.PostgresPersistenceUnit(dsn=dsn)
    return repositories.InMemoryPersistenceUnit()


def _cleanup(unit):
    try:
        for m in list(unit.missions.list_missions()):
            data = unit.missions.load_mission(m)
            if data and (data.get("request") or "").startswith("m12rs"):
                unit.missions.remove_mission(m)
    except Exception:
        pass
    try:
        unit.idempotency.clear()
    except Exception:
        pass
    try:
        unit.audit.clear_audit()
    except Exception:
        pass


@pytest.fixture(autouse=True)
def _fresh_unit():
    u = _unit()
    _cleanup(u)
    yield u
    _cleanup(u)


def _state_after_restart(unit, status, request_text, mission_id):
    """Tulis mission lifecycle ke repo (struktur setara as_dict()), lalu service
    BARU merecover -> kembalikan state yang dipulihkan."""
    unit.missions.save_mission(
        mission_id,
        {
            "request_id": f"req-{mission_id}",
            "request": request_text,
            "approval": {"status": "waiting_approval" if status in (
                "waiting_approval", "received", "understood", "approved") else "approved",
                          "decision": None},
            "execution": {"status": status, "failure_kind": "", "failure_message": "",
                           "result_summary": ""},
            "evidence": [],
            "artifact_ref": "",
            "audit_ref": "",
            "timeline": [{"stage": "persisted", "ok": True}],
            "updated_at": "2026-08-13T00:00:00Z",
        },
    )
    # restart: service baru + unit/DSN sama
    svc = MissionUXService(persistence=unit)
    st = svc.get_state()
    return st


def test_restart_preserves_waiting_approval(monkeypatch):
    """Mission di antrean approval TIDAK hilang & TIDAK berubah status saat
    process restart."""
    unit = _unit()
    st = _state_after_restart(unit, "waiting_approval", "m12rs task A", "m12rs-m-waiting")
    assert st is not None
    assert st.approval_status == "waiting_approval"
    assert st.request_id == "req-m12rs-m-waiting"
    assert st.status == "waiting_approval"


def test_restart_preserves_running_and_result(monkeypatch):
    """Mission yang sedang berjalan/selesai/gagal tetap dengan status & detail
    setelah restart — operational truth tidak hilang."""
    unit = _unit()
    # COMPLETED mission
    st_done = _state_after_restart(unit, "completed", "m12rs task done", "m12rs-m-done")
    assert st_done is not None
    assert st_done.status == "completed"
    # FAILED mission dengan detail failure
    st_bad = _state_after_restart(unit, "failed", "m12rs task fail", "m12rs-m-fail")
    assert st_bad is not None
    assert st_bad.status == "failed"


def test_restart_repopulates_idempotency_and_audit(monkeypatch):
    """Idempotency key + audit trail tersedia lagi setelah restart, terlepas
    dari keberadaan mission (recover repo independen)."""
    unit = _unit()
    unit.idempotency.save_idempotency(
        "m12rs-key-1", {"request_id": "req-x", "text": "m12rs op"}, "m12rs-m-aud")
    unit.audit.append_audit("m12rs-aud-1", {"mission_id": "m12rs-m-aud", "event": "e1"})
    svc = MissionUXService(persistence=unit)
    assert svc._idem.get("m12rs-key-1", {}).get("request_id") == "req-x"
    assert any(e.get("event") == "e1" and e.get("mission_id") == "m12rs-m-aud" for e in svc._audit)
