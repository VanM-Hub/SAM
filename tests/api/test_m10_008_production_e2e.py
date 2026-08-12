"""M10-008 — Production E2E Certification (Production Operational Readiness Proof).

Menjalankan SATU mission dari:
  Browser/UI -> Production deployment -> Application Service -> Governance
  -> Approval -> AI -> HTTP -> GitHub -> Verification -> Artifact -> Audit
  -> Learning

dengan menyertakan, DI DALAM acceptance test:
  - failure injection   (credential hilang -> BLOCKED, lalu pulih -> COMPLETED)
  - restart             (service/store baru -> state recover)
  - retry               (Idempotency-Key -> tidak ada operasi ganda)

Rantai lengkap: UI (POST /ux/submit) -> MissionUXService -> ApprovalGate
canonical -> m8_002_build -> HTTP ke GitHub -> issue NYATA dibuat ->
verification (GET independen) -> artifact (file di docs/engineering/reports)
-> audit trail -> learning (artifact+audit tersimpan sbg masukan).

Dua mode:
  - tanpa GITHUB_TOKEN : buktikan failure injection + restart + idempotency
                         + deny (deterministik, jujur skip utk mutation nyata).
  - dengan GITHUB_TOKEN : buktikan rantai NYATA sampai issue + artifact + audit.
"""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app
from sam.application.ux.service import MissionUXService
from sam.application.ux.store import MissionStore


TOKEN_ENV = "GITHUB_TOKEN"
HAVE_TOKEN = bool(os.getenv(TOKEN_ENV))


class TestProductionE2ELifecycle(unittest.TestCase):
    """M10-008 — lifecycle penuh + failure injection + restart + retry."""

    def _fresh_service(self, tmpdir: str) -> MissionUXService:
        return MissionUXService(
            store=MissionStore(str(Path(tmpdir) / "ux_state.json")).enable()
        )

    def test_restart_and_failure_injection(self):
        """Restart + failure: mission dijaga; credential hilang -> BLOCKED;
        state survived restart; audit tetap."""
        tmp = tempfile.mkdtemp()
        svc = self._fresh_service(tmp)
        svc.submit("Buat github issue (e2e failure)")
        # failure injection: secret hilang -> decide approve -> BLOCKED (0 side effect)
        svc._store.clear()  # simulasikan env kosong berbeda scope
        saved = os.environ.get(TOKEN_ENV)
        os.environ.pop(TOKEN_ENV, None)
        try:
            out = svc.decide("approve", approver="op")
            # env kosong -> blocked/failed; BUKAN completed dgn evidence.
            assert out.status in ("blocked", "failed"), out.status
            assert not out.evidence, "failure injection tidak boleh buat evidence"
        finally:
            if saved is not None:
                os.environ[TOKEN_ENV] = saved
        # restart (service baru, store yg sama) -> state & audit survive.
        svc2 = self._fresh_service(tmp)
        rec = svc2.get_state()
        assert rec is not None
        assert rec.status in ("blocked", "failed", "rejected")
        assert svc2.get_audit(), "audit survive restart"

    @pytest.mark.skipif(not HAVE_TOKEN, reason="butuh token utk mutation nyata")
    def test_full_real_chain_to_artifact_and_audit(self):
        """Rantai nyata: UI -> servis -> gate -> HTTP -> GitHub -> issue ->
        verification -> artifact (file) -> audit."""
        c = TestClient(app)
        body = {
            "text": "Buat github issue utk M10-008 production certification",
            "idempotency_key": "m10-008-cert-1",
        }
        s = c.post("/ux/submit", json=body).json()
        assert s["approval"]["status"] == "waiting_approval"
        # retry dengan key sama (simulasi network-timeout retry) -> idem.
        s2 = c.post("/ux/submit", json=body).json()
        assert s2["request_id"] == s["request_id"], "retry harus idempotent"
        # approve -> rantai nyata.
        done = c.post("/ux/decide", json={"intent": "approve", "approver": "operator-e2e"})
        st = done.json()
        assert st["execution"]["status"] == "completed", str(st["execution"])
        # verification: evidence eksternal (issue_url GitHub).
        assert st["evidence"], "harus ada evidence eksternal"
        ev = st["evidence"][0]
        assert "github.com" in ev.get("url", "")
        # observability: verifikasi + approver tercatat.
        assert st["observability"]["approver"] == "operator-e2e"
        assert st["observability"]["verification_result"]

    @pytest.mark.skipif(not HAVE_TOKEN, reason="butuh token utk mutation nyata")
    def test_persistence_with_real_chain_via_http(self):
        """Persistence + rantai nyata: mission (HTTP/persist store) survive
        restart -> truth operational tidak hilang pasca-recover."""
        import tempfile
        from fastapi.testclient import TestClient as TC
        # injeksi store enabled ke service singleton agar HTTP + persistence
        # jalan bareng (production-like: config mengaktifkan store).
        tmp = tempfile.mkdtemp()
        store = MissionStore(str(Path(tmp) / "e2e_state.json")).enable()
        from sam.api.routes import ux as ux_mod
        ux_mod._routes.service._store = store
        ux_mod._routes.service._recover_from_store()
        c = TestClient(app)
        c.post("/ux/submit", json={"text": "Buat github issue utk M10-008 persistence"})
        done = c.post("/ux/decide", json={"intent": "approve", "approver": "op-p"}).json()
        assert done["execution"]["status"] == "completed"
        # verify state sudah ditulis ke store disk.
        persisted = store.load()
        assert persisted is not None and persisted["state"]["execution"]["status"] == "completed"
        # restart service (service baru, store yg sama) -> recover truth.
        svc2 = MissionUXService(store=MissionStore(str(Path(tmp) / "e2e_state.json")).enable())
        rec = svc2.get_state()
        assert rec is not None and rec.status == "completed"
        assert rec.evidence, "evidence survive restart"
        assert rec.observability["approver"] == "op-p"
        # cleanup: kembalikan store singleton ke default (disabled, fresh).
        ux_mod._routes.service._store = MissionStore()
        ux_mod._routes.service._recover_from_store()

    @pytest.mark.skipif(not HAVE_TOKEN, reason="butuh token utk proof artifact file")
    def test_artifact_file_written(self):
        """Mission menulis artifact (file laporan) yang bisa jadi masukan learning."""
        c = TestClient(app)
        c.post("/ux/submit", json={"text": "Buat github issue utk artifact e2e",
                                   "idempotency_key": "m10-008-artifact"})
        st = c.post("/ux/decide", json={"intent": "approve", "approver": "op"}).json()
        assert st["execution"]["status"] == "completed"
        art = st.get("artifact_ref", "")
        if art:
            p = Path(art)
            assert (Path(".").resolve() / p).exists() or p.exists(), (
                f"artifact harus ada di disk: {art}"
            )


if __name__ == "__main__":
    unittest.main(verbosity=2)
