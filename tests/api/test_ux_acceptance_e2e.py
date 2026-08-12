"""M9-003/004/005 Acceptance — dua perjalanan user lengkap (UI-equivalent E2E).

Membuktikan perjalanan sesuai acceptance Van, melalui jalur UI -> /ux (HTTP)
yang sama dengan browser (fetch ke /ux, bukan ke GitHub):

  Skenario 1 (real mutation):
    Open UI -> Submit -> UI menerima state -> SAM susun plan -> UI tampil approval
    -> Click APPROVE -> POST /ux/decide -> ApprovalGate canonical -> GitHub real
    mutation -> GET GitHub verify -> UI tampil hasil -> Evidence visible -> Audit visible

  Skenario 2 (reject = 0 mutation):
    Submit -> Reject -> /ux/decide reject -> REJECTED -> GitHub mutation count = 0

Tanpa GITHUB_TOKEN di env, skenario 1 di-skip (jujur, bukan fake pass).
"""
from __future__ import annotations

import os
import unittest

import httpx
import pytest
from fastapi.testclient import TestClient

from sam.api.server import app


TOKEN_ENV = "GITHUB_TOKEN"
HAVE_TOKEN = bool(os.environ.get(TOKEN_ENV))
TEST_REPO = os.environ.get("GITHUB_TEST_REPO") or "VanM-Hub/test-issues"


def _github_issue_count() -> int:
    """Hitung open issue di repo test via API eksternal."""
    h = {
        "Authorization": "Bearer " + os.environ[TOKEN_ENV],
        "Accept": "application/vnd.github+json",
    }
    r = httpx.get(
        f"https://api.github.com/repos/{TEST_REPO}/issues?state=open&per_page=100",
        headers=h, timeout=20,
    )
    assert r.status_code == 200, f"github count failed: {r.status_code}"
    return len(r.json())


@pytest.fixture
def client():
    c = TestClient(app)
    yield c
    # reset state global antar test (instanceservice singleton route) — tak ada
    # reset publik; tiap skenario gunakan request text unik & asersi final state
    # cukup dari respons langsung, tidak bergantung state global antar-skenario.


def _submit(client, text: str):
    return client.post("/ux/submit", json={"text": text})


class TestApprovalJourneyReal(unittest.TestCase):
    """Skenario 1: approve -> real mutation -> verify -> evidence -> audit."""

    def setUp(self):
        self.client = TestClient(app)

    @pytest.mark.skipif(not HAVE_TOKEN, reason="GITHUB_TOKEN tidak ada -> skip honest")
    def test_approve_full_journey(self):
        text = "Buat GitHub issue lewat jalur user (acceptance m9)"
        # 1) submit
        r = self.client.post("/ux/submit", json={"text": text})
        assert r.status_code == 200
        s = r.json()
        assert s["approval"]["status"] == "waiting_approval"
        assert s["execution"]["status"] == "waiting_approval"
        assert s["plan"]["approval_required"] is True
        assert "SAM memahami" in s["understanding"]["what_sam_understood"]
        assert s["plan"]["planned_steps"]  # plan nyata, bukan kosong

        # 2) approve -> real gate -> real execution
        r = self.client.post("/ux/decide", json={"intent": "approve", "approver": "user"})
        assert r.status_code == 200
        s = r.json()
        assert s["execution"]["status"] == "completed", (
            "approve harus menghasilkan completed (real), bukan fake: " + str(s["execution"])
        )
        # 3) evidence external nyata (issue_url)
        assert s["evidence"], "harus ada evidence eksternal setelah approve"
        ev = s["evidence"][0]
        assert ev["kind"] == "external_github_issue"
        assert "github.com" in ev.get("url", "")
        assert ev.get("number") is not None
        # 4) artifact + audit tersedia
        assert s["artifact_ref"]
        assert s["audit_ref"]
        # 5) tidak bocor secret
        blob = str(s).lower()
        for marker in ("ghp_", "sk-", "bearer "):
            assert marker not in blob, f"state bocor {marker}"

    def test_submit_plan_human_language(self):
        """Bahkan tanpa token: submit -> plan + approval gate (state nyata)."""
        r = _submit(self.client, "Buat GitHub issue untuk cek rencana")
        assert r.status_code == 200
        s = r.json()
        assert s["plan"]["planned_steps"]
        assert s["approval"]["status"] == "waiting_approval"
        # bahasa manusia, bukan jargon internal
        assert "MCR" not in str(s["plan"].get("action_summary", ""))  # plan pakai bahasa manusia


class TestRejectNoMutation(unittest.TestCase):
    """Skenario 2: reject -> REJECTED -> TIDAK ada eksekusi/evidence/mutation."""

    def setUp(self):
        self.client = TestClient(app)

    @pytest.mark.skipif(not HAVE_TOKEN, reason="butuh token utk membuktikan 0 mutation nyata")
    def test_reject_produces_no_mutation(self):
        # Sedikit jeda sebelum & sesudah utk men-stabilkan eventual consistency
        # API GitHub: issue yang dibuat test approve lain (dalam suite yang sama)
        # baru muncul di count beberapa saat kemudian. Guna menghindari flake
        # dari lag, settle dulu sebelum hitung before.
        import time as _t
        _t.sleep(3)
        before = _github_issue_count()
        _t.sleep(2)
        before = _github_issue_count()
        text = "Buat GitHub issue yang tidak boleh jadi (harus 0 mutation)"
        r = self.client.post("/ux/submit", json={"text": text})
        assert r.status_code == 200
        s = r.json()
        assert s["approval"]["status"] == "waiting_approval"

        r = self.client.post("/ux/decide", json={"intent": "reject", "approver": "user"})
        assert r.status_code == 200
        s = r.json()
        # REJECTED, bukan completed/blocked/failed
        assert s["execution"]["status"] == "rejected"
        assert s["execution"]["failure_kind"] == "rejected"
        assert s["approval"]["status"] == "rejected"
        # TIDAK ada evidence eksternal (0 mutation) & tidak ada artifact mission result
        assert not s["evidence"], "reject TIDAK boleh menghasilkan evidence eksternal"
        # audit memuat keputusan reject, bukan real execute
        aud = self.client.get("/ux/audit").json().get("audit") or []
        assert aud, "audit harus ada"
        # tidak ada stage real mutation di timeline
        for e in s.get("timeline") or []:
            assert e.get("stage") != "execute", "timeline tidak boleh memuat eksekusi nyata saat reject"
        # BUKTI EKSTERNAL: jumlah issue GitHub TIDAK bertambah dari operasi reject ini.
        _t.sleep(2)
        after = _github_issue_count()
        assert after == before, (
            f"reject harus menghasilkan 0 mutation: issue count {before} -> {after}"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
