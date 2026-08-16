"""M10-003 — Observability: operator bisa menjawab "SAM lakukan apa, mengapa,
atas persetujuan siapa, ke sistem mana, bagaimana tahu hasil benar".

Setiap real operation wajib punya (tanpa secret leakage):
    request_id / mission_id / execution_id / capability / external_target
    start_time / end_time / status / verification_result / failure_reason
    approver

Test membaca blok `observability` dari state (/ux/state) — jalur HTTP yang sama
dengan yang dilihat operator/UI. Tanpa secret leakage (observability murni
metadata operasional).
"""
from __future__ import annotations

import os
import unittest

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app


TOKEN_ENV = "GITHUB_TOKEN"
HAVE_TOKEN = bool(os.getenv(TOKEN_ENV))

REQUIRED_FIELDS = [
    "request_id", "mission_id", "execution_id", "capability",
    "external_target", "start_time", "end_time", "status",
    "verification_result", "failure_reason", "approver",
]


@pytest.fixture(autouse=True)
def _protect_token_for_acceptance():
    """Isolasi env: test lain mungkin me-*pop* GITHUB_TOKEN; pastikan tiap test
    M10-003 yang butuh token punya nilai dari env asli saat import (bukan
    bergantung pada exec env yang bisa di-override antar test file)."""
    original = os.environ.get(TOKEN_ENV)
    if original:
        os.environ[TOKEN_ENV] = original
    yield


def _submit(c, text="Buat github issue utk observability"):
    r = c.post("/ux/submit", json={"text": text})
    assert r.status_code == 200
    s = r.json()
    assert s["observability"]["mission_id"].startswith("mission-")
    return s


def _mid(s):
    return s["observability"]["mission_id"]


def _decide(c, mid, intent="reject", approver="operator-a"):
    return c.post("/ux/decide", json={"intent": intent, "mission_id": mid, "approver": approver})


class TestObservability(unittest.TestCase):
    """M10-003 — blok observability lengkap & konsisten."""

    def test_submit_has_full_observability(self):
        """Setelah submit, observability memuat semua field (kecuali terminal)."""
        c = TestClient(app)
        s = _submit(c)
        obs = s.get("observability") or {}
        for f in REQUIRED_FIELDS:
            assert f in obs, f"observability kurang field: {f}"
        assert obs["request_id"]
        assert obs["mission_id"].startswith("mission-")
        assert obs["capability"]  # github / dsb
        assert obs["external_target"]
        assert obs["start_time"]
        assert obs["status"] == "waiting_approval"
        # belum dijalankan -> belum ada execution_id / end_time / verifikasi
        assert obs["execution_id"] == ""
        assert obs["end_time"] == ""
        assert obs["verification_result"] == ""

    def test_reject_records_approver_and_no_execution(self):
        """Reject -> observability mencatat approver, 0 mutation, no exec."""
        c = TestClient(app)
        s0 = _submit(c)
        r = _decide(c, _mid(s0), "reject", "operator-a")
        s = r.json()
        obs = s["observability"]
        assert obs["status"] == "rejected"
        assert obs["approver"] == "operator-a"
        assert obs["verification_result"] == "none (ditolak, 0 mutation)"
        assert obs["failure_reason"]
        assert obs["end_time"]
        assert obs["execution_id"] == "", "reject tidak boleh punya execution_id"

    def test_approver_in_audit_timeline(self):
        """Timeline/audit mencatat approver utk pertanyaan 'atas persetujuan siapa'."""
        c = TestClient(app)
        s0 = _submit(c)
        _decide(c, _mid(s0), "reject", "operator-b")
        aud = (c.get("/ux/audit").json() or {}).get("audit") or []
        assert any(e.get("approver") == "operator-b" for e in aud), (
            "audit harus mencatat approver"
        )

    @pytest.mark.skipif(not HAVE_TOKEN, reason="butuh token utk approve nyata")
    def test_approve_has_execution_id_and_verification(self):
        """Approve -> execution_id + end_time + verification_result terisi."""
        c = TestClient(app)
        s0 = _submit(c, "Buat github issue utk observability approve")
        r = _decide(c, _mid(s0), "approve", "operator-c")
        s = r.json()
        assert s["execution"]["status"] == "completed"
        obs = s["observability"]
        assert obs["status"] == "completed"
        assert obs["execution_id"].startswith("exec-")
        assert obs["approver"] == "operator-c"
        assert obs["end_time"], "approve harus punya end_time"
        assert obs["verification_result"], "approve harus punya verification_result"
        assert obs["failure_reason"] == ""

    def test_observability_never_leaks_secret(self):
        """Observability (metadata) TIDAK pernah memuat secret."""
        c = TestClient(app)
        s = _submit(c)
        blob = str(s.get("observability")).lower()
        for marker in ("ghp_", "sk-", "nvapi-", "bearer ", "token="):
            assert marker not in blob, f"observability bocor {marker}"

    def test_operator_question_answerable_from_state(self):
        """Semua elemen jawaban operator tersedia di /ux/state (tanpa GitHub)."""
        # Pertanyaan Van: "SAM lakukan apa pukul 10:42, mengapa, atas persetujuan
        # siapa, ke sistem mana, dan bagaimana tahu hasil benar?"
        c = TestClient(app)
        s = _submit(c)
        # apa        -> operation/capability
        assert s["understanding"]["operation"]
        # ke mana     -> external_target
        st = c.get("/ux/state").json()
        assert st["observability"]["external_target"]
        # mengapa     -> what_sam_understood (rencana)
        assert st["understanding"]["what_sam_understood"]
        # kapan       -> start_time
        assert st["observability"]["start_time"]
        # persetujuan -> approval.status + approver (ada di decision utk terminal)
        assert st["approval"]["status"] in ("waiting_approval", "approved", "rejected")


if __name__ == "__main__":
    unittest.main(verbosity=2)
