"""M10-007 — Persistence: restart TIDAK menghilangkan operational truth.

Syarat Van:
    Mission -> Execution -> Restart SAM -> Recover state -> Continue/reconcile
    -> Verify

Penting utk: Mission; Approval; Execution; Evidence; Audit; Learning.

Implementasi: `MissionStore` (JSON atomik di disk) + `MissionUXService`
me-persist state pada tiap mutasi (submit/decide) dan me-recover saat
`__init__`. State/audit yang dipersist TIDAK pernah memuat secret.

Test memakai store sementara (tmp path) yg di-clear per-test, dan menjalankan
service "baru" (restart) yg me-load dari store yang sama.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

from sam.application.ux.service import MissionUXService
from sam.application.ux.store import MissionStore


class TestMissionStore(unittest.TestCase):
    """M10-007 — store menulis & membaca snapshot secara deterministik."""

    def _tmp(self) -> MissionStore:
        d = tempfile.mkdtemp()
        return MissionStore(str(Path(d) / "ux_state.json")).enable(), d

    def test_save_then_load_roundtrip(self):
        store, _ = self._tmp()
        payload = {"version": 1, "state": {"request_id": "req-x"},
                   "audit": [{"stage": "approval"}], "idem": {}}
        store.save(payload)
        loaded = store.load()
        assert loaded is not None
        assert loaded["state"]["request_id"] == "req-x"
        assert loaded["audit"][0]["stage"] == "approval"

    def test_load_missing_returns_none(self):
        store = MissionStore(str(Path(tempfile.mkdtemp()) / "nope.json"))
        assert store.load() is None


class TestServicePersistence(unittest.TestCase):
    """M10-007 — state service survive restart (recover dari store)."""

    def _make(self, tmpdir: str) -> MissionUXService:
        return MissionUXService(
            store=MissionStore(str(Path(tmpdir) / "ux_state.json")).enable()
        )

    def test_reject_state_persists_and_recovers(self):
        tmp = tempfile.mkdtemp()
        svc = self._make(tmp)
        st = svc.submit("Buat github issue (persist reject)")
        svc.decide("reject", approver="op-1")
        assert svc.get_state().status == "rejected"
        assert svc.get_state().observability["approver"] == "op-1"

        # restart: service BARU memakai store yang sama -> recover state reject.
        svc2 = self._make(tmp)
        recovered = svc2.get_state()
        assert recovered is not None
        assert recovered.request_id == st.request_id
        assert recovered.status == "rejected"
        assert recovered.observability["approver"] == "op-1"

    def test_waiting_approval_persists_and_recovers(self):
        tmp = tempfile.mkdtemp()
        svc = self._make(tmp)
        svc.submit("Buat github issue (persist waiting)")
        svc2 = self._make(tmp)  # restart sebelum approve
        rec = svc2.get_state()
        assert rec is not None
        assert rec.approval_status == "waiting_approval"
        assert rec.request_id

    def test_audit_persists_across_restart(self):
        tmp = tempfile.mkdtemp()
        svc = self._make(tmp)
        svc.submit("Buat github issue (audit persist)")
        svc.decide("reject", approver="op-2")
        aud_before = svc.get_audit()
        assert aud_before, "harus ada audit"
        svc2 = self._make(tmp)
        aud_after = svc2.get_audit()
        assert len(aud_after) == len(aud_before), (
            "audit harus survive restart: same count"
        )
        assert aud_after[0].get("stage") == "approval"

    def test_persisted_state_never_contains_secret(self):
        tmp = tempfile.mkdtemp()
        svc = self._make(tmp)
        svc.submit("Buat github issue (secret check)")
        svc.decide("reject", approver="op")
        payload = svc._store.load()
        blob = str(payload).lower()
        for marker in ("ghp_", "sk-", "nvapi-", "bearer "):
            assert marker not in blob, f"persisted state bocor {marker}"

    def test_operator_truth_survives_restart(self):
        """Jawaban 'SAM lakukan apa/kapan/kenapa/dst' survive restart."""
        tmp = tempfile.mkdtemp()
        svc = self._make(tmp)
        svc.submit("Buat github issue utk truth")
        svc.decide("reject", approver="op-final")
        svc2 = self._make(tmp)
        obs = svc2.get_state().observability
        assert obs["status"] == "rejected"
        assert obs["approver"] == "op-final"
        assert obs["start_time"], "kapan SAM mulai (start_time) survive"
        assert obs["end_time"], "kapan SAM selesai (end_time) survive"


if __name__ == "__main__":
    unittest.main(verbosity=2)
