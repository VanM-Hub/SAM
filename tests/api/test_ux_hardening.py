"""M9-008 — Operational Workspace Hardening (UI vertical slice ke production).

Membuktikan UI yang di-serve adalah THIN CLIENT jujur (source of truth = server),
bukan demo/prototype:

  M9-008.1  Tidak ada prototype/fake/preview/mock semantics yang operational.
  M9-008.2  UI merepresentasikan state canonical; TIDAK menciptakan state sendiri.
  M9-008.4  Refresh/reload resilience: state + evidence + audit tetap ada dari
            server (bukan JS memory/session/localStorage).
  M9-008.5  Failure semantics: BLOCKED/FAILED/REJECTED/COMPLETED benar & konsisten
            UI(state via /ux/state) == runtime state.

Semua data teruji lewat jalur HTTP yang SAMA dengan browser (fetch ke /ux server).
Test yang butuh GITHUB_TOKEN di-skip jujur (bukan fake pass) di CI tanpa token.
"""
from __future__ import annotations

import os
import re
import unittest

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app


TOKEN_ENV = "GITHUB_TOKEN"
HAVE_TOKEN = bool(os.environ.get(TOKEN_ENV))


# Ambil UI real yang di-serve dari server (bukan file lokal) — bukti HTTP-serve,
# bukan sekadar statik.
def _served_ui() -> str:
    c = TestClient(app)
    r = c.get("/ui")
    assert r.status_code == 200, f"/ui harus 200, dapat {r.status_code}"
    return r.text


class TestNoPrototypeSemantics(unittest.TestCase):
    """M9-008.1 — tidak ada fake/preview/mock operational semantics."""

    def test_ui_is_thin_client_to_ux_only(self):
        """Browser hanya fetch ke /ux — TIDAK pernah langsung ke GitHub/eksternal."""
        ui = _served_ui()
        # Semua fetch ke server (/ux/*, /health, /runtime, /knowledge, dst).
        # DILARANG ada fetch/axios ke api.github.com / nvidia / eksternal lain.
        for pat in (
            r"fetch\(\s*['\"]https?://",
            r"api\.github\.com",
            r"api\.nvidia",
            r"apps\.nvidia",
            r"https?://[^'\"]*github\.com/[^'\"]*issues",
        ):
            assert not re.search(pat, ui, flags=re.I), (
                f"UI tidak boleh akses eksternal langsung: pola {pat}"
            )

    def test_no_preview_mode_state_creator(self):
        """Tidak ada state 'preview mode' yang menciptakan state sendiri."""
        ui = _served_ui()
        # 'previewMode' sebagai object/state harus tidak ada (sudah dihapus).
        assert "previewMode" not in ui, "previewMode tidak boleh ada di UI"
        # '0 external calls' adalah indikator preview masquerading — harus tiada.
        assert "0 external calls" not in ui

    def test_no_fake_operational_controls(self):
        """Tidak ada tombol fake ('Preview Mode', 'Pause' sebagai simulasi).
        Kontrol keputusan nyata: ada jalur tolak (decide reject) -> canonical."""
        ui = _served_ui()
        # Tombol tolak nyata (reject intent ke canonical ApprovalGate).
        # (HTML membawa escaping di JS string; cocokkan cukup 'reject' pada panggilan decide)
        assert re.search(r"decide\([\\']*reject", ui), "harus ada kontrol tolak nyata (reject intent)"
        for pat in (r">Preview Mode<", r">Pause<", r">Simulasi<"):
            assert not re.search(pat, ui), f"unsur fake/simulasi: {pat}"

    def test_state_source_is_server_not_localstorage(self):
        """Source of truth = server. localStorage/sessionStorage TIDAK jadi state."""
        ui = _served_ui()
        assert "localStorage" not in ui, "localStorage tidak boleh source of truth"
        assert "sessionStorage" not in ui, "sessionStorage tidak boleh source of truth"
        # Semua interaksi misi lewat /ux (server), bukan DOM-append mandiri.
        assert "/ux/submit" in ui and "/ux/decide" in ui


class TestStateMachineUX(unittest.TestCase):
    """M9-008.2 — UI merepresentasikan state canonical; tidak menciptakan state."""

    def test_ui_reads_state_from_ux(self):
        """UI membaca mission state dari GET /ux/state (bukan JS buatan)."""
        ui = _served_ui()
        assert "/ux/state" in ui, "UI harus memanggil /ux/state untuk state mission"
        assert "/ux/evidence" in ui, "UI harus memanggil /ux/evidence"
        assert "/ux/audit" in ui, "UI harus memanggil /ux/audit"
        # Tidak ada object yang hardcode status mission selesai.
        assert "lastResult = { status: 'completed'" not in ui

    @pytest.mark.skipif(not HAVE_TOKEN, reason="butuh token utk state terminal real")
    def test_terminal_state_from_runtime_not_ui(self):
        """Setelah approve, state terminal (completed) datang dari runtime /ux/state,
        dan request berikutnya (simulasi refresh) tetap 'completed'."""
        c = TestClient(app)
        c.post("/ux/submit", json={"text": "Buat github issue untuk state canonical"})
        r = c.post("/ux/decide", json={"intent": "approve", "approver": "user"})
        assert r.status_code == 200
        s = r.json()
        assert s["execution"]["status"] == "completed"
        # "refresh/resume": request baru (GET /ux/state) tetap completed dari server.
        r2 = TestClient(app).get("/ux/state")
        assert r2.status_code == 200
        d = r2.json()
        assert d["request_id"] == s["request_id"]
        assert d["execution"]["status"] == "completed"


class TestRefreshResilience(unittest.TestCase):
    """M9-008.4 — refresh tidak menghilangkan state; tidak bergantung JS memory."""

    def test_submit_state_persists_across_requests(self):
        """submit -> state waiting_approval; request berikutnya (simulasi refresh)
        tetap waiting_approval — bukan hilang karena JS reset."""
        c = TestClient(app)
        post = c.post("/ux/submit", json={"text": "Buat github issue untuk refresh test"})
        assert post.status_code == 200
        sid = post.json()["request_id"]
        # "refresh" = request HTTP baru yg sama (server singleton memegang state).
        refresh = TestClient(app).get("/ux/state")
        assert refresh.status_code == 200
        d = refresh.json()
        assert d["request_id"] == sid
        assert d["approval"]["status"] == "waiting_approval"
        # plan & understanding tetap tersedia pasca refresh.
        assert d["plan"]["planned_steps"]
        assert d["understanding"]["what_sam_understood"]

    def test_ui_hydrates_from_server(self):
        """UI tidak hanya mengandalkan JS: ia me-rehydrate dari /ux/state di init.
        Implementasi v18: loadState() membaca /ux/state; renderWorkspace dari state itu."""
        ui = _served_ui()
        assert "loadState" in ui, "UI harus punya loadState (rehydrate dari server)"
        assert "/ux/state" in ui
        assert "renderWorkspace" in ui

    @pytest.mark.skipif(not HAVE_TOKEN, reason="butuh token utk proof evidence pasca-refresh")
    def test_evidence_audit_available_after_refresh(self):
        """Setelah approve, GET /ux/evidence & /ux/audit (request terpisah = refresh)
        tetap mengembalikan data — evidence/audit dari runtime, bukan JS session."""
        c = TestClient(app)
        c.post("/ux/submit", json={"text": "Buat github issue evidence refresh"})
        done = c.post("/ux/decide", json={"intent": "approve", "approver": "user"})
        assert done.status_code == 200
        assert done.json()["execution"]["status"] == "completed"

        ev = TestClient(app).get("/ux/evidence").json().get("evidence") or []
        assert ev, "evidence harus tetap tersedia pasca refresh (dari runtime)"
        aud = TestClient(app).get("/ux/audit").json().get("audit") or []
        assert aud, "audit harus tetap tersedia pasca refresh (dari runtime)"
        # tidak bocor secret di evidence/audit
        blob = str(ev).lower() + str(aud).lower()
        for marker in ("ghp_", "sk-", "bearer "):
            assert marker not in blob, f"evidence/audit bocor {marker}"


class TestFailureRecoveryUX(unittest.TestCase):
    """M9-008.5 — BLOCKED/FAILED/REJECTED/COMPLETED benar; UI state == runtime."""

    def test_rejected_maps_from_runtime(self):
        """Reject -> REJECTED dari runtime; /ux/state konsisten (UI == runtime)."""
        c = TestClient(app)
        c.post("/ux/submit", json={"text": "Buat github issue untuk dicoba tolak"})
        r = c.post("/ux/decide", json={"intent": "reject", "approver": "user"})
        assert r.status_code == 200
        s = r.json()
        assert s["execution"]["status"] == "rejected"
        st2 = TestClient(app).get("/ux/state").json()
        assert st2["execution"]["status"] == "rejected", "UI state harus == runtime"
        assert s["execution"]["failure_kind"] == "rejected"

    def test_html_renders_failure_semantics_from_runtime(self):
        """UI menampilkan BLOCKED/FAILED/REJECTED/COMPLETED dari runtime data,
        bukan hardcoded — renderWorkspace membaca state.execution.failure_message."""
        ui = _served_ui()
        assert "state.execution.failure_message" in ui, "UI harus render failure_message dari runtime"
        assert "renderWorkspace" in ui
        assert "effStatus" in ui
        # status terminal dipetakan dari runtime (blocked/failed/rejected/completed)
        assert "BLOCKED" in ui and "FAILED" in ui and "REJECTED" in ui and "COMPLETED" in ui


if __name__ == "__main__":
    unittest.main(verbosity=2)
