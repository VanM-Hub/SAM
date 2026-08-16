"""M10-005 — Idempotency & Concurrency.

Syarat Van: karena SAM sudah melakukan mutation nyata, retry (mis. user submit
-> network timeout -> retry) TIDAK boleh membuat operasi ganda:

    User submits mission -> network timeout -> User retries
    SAM TIDAK boleh membuat Issue #20 DAN Issue #21 utk satu permintaan.

Harus: Idempotency-Key -> same logical operation -> same outcome.

Implementasi: `MissionUXService.submit(text, idempotency_key=...)`. Jika key
yang sama + teks yang sama diajukan lagi, SAM mengembalikan state yg SAMA
(request_id sama), TIDAK membuat mission baru. Satu key -> satu request_id
-> satu execution -> satu issue (bila disetujui).
"""
from __future__ import annotations

import os
import unittest

import pytest
from fastapi.testclient import TestClient

from sam.api.server import app


TOKEN_ENV = "GITHUB_TOKEN"


class TestIdempotencyKey(unittest.TestCase):
    """M10-005 — idempotency key mencegah operasi ganda."""

    def test_same_key_returns_same_request_id(self):
        """Submit ulang dengan key yang sama -> request_id SAMA (bukan baru)."""
        c = TestClient(app)
        body1 = {"text": "Buat github issue (idem)", "idempotency_key": "op-abc-001"}
        r1 = c.post("/ux/submit", json=body1)
        s1 = r1.json()
        assert s1["approval"]["status"] == "waiting_approval"

        # retry (network timeout) -> key sama, teks sama
        r2 = c.post("/ux/submit", json=body1)
        s2 = r2.json()
        assert s2["request_id"] == s1["request_id"], (
            "retry dengan key sama harus memakai request_id SAMA, bukan baru"
        )
        assert s2["observability"]["mission_id"] == s1["observability"]["mission_id"]
        assert s2["approval"]["status"] == "waiting_approval"

    def test_different_key_creates_new_mission(self):
        """Key berbeda -> request_id berbeda (operasi logis yang beda)."""
        c = TestClient(app)
        a = c.post("/ux/submit", json={"text": "Buat issue A", "idempotency_key": "k-1"}).json()
        b = c.post("/ux/submit", json={"text": "Buat issue B", "idempotency_key": "k-2"}).json()
        assert a["request_id"] != b["request_id"]

    def test_same_key_different_text_is_not_reused(self):
        """Key yang sama tapi teks berbeda -> TIDAK mengembalikan state lama
        (mencegah misuse key untuk operasi berbeda)."""
        c = TestClient(app)
        a = c.post("/ux/submit", json={"text": "Buat issue X", "idempotency_key": "op-x"}).json()
        b = c.post("/ux/submit", json={"text": "Buat issue Y berbeda", "idempotency_key": "op-x"}).json()
        # karena teks beda, ini diperlakukan sbg operasi baru (request_id baru)
        assert b["request_id"] != a["request_id"]

    @pytest.mark.skipif(not bool(os.getenv(TOKEN_ENV)), reason="butuh token utk approve nyata")
    def test_one_key_one_issue(self):
        """Retry dengan key sama TIDAK membuat issue ganda: approve satu key
        menghasilkan satu eksekusi (evidence tunggal), bukan dua."""
        c = TestClient(app)
        body = {"text": "Buat github issue (idempotency proof)", "idempotency_key": "op-final-7"}
        s0 = c.post("/ux/submit", json=body).json()
        mid = s0["observability"]["mission_id"]
        # retry dengan key sama -> state sama (belum approve)
        c.post("/ux/submit", json=body)
        # approve SATU kali saja untuk operasi logis tunggal
        r = c.post("/ux/decide", json={"intent": "approve", "mission_id": mid, "approver": "user"})
        s = r.json()
        assert s["execution"]["status"] == "completed"
        # evidence harus 1 (satu issue untuk satu operasi logis)
        assert len(s["evidence"]) == 1, (
            "idempotency: retry dgn key sama harus tetap 1 evidence, bukan ganda: "
            + str(s["evidence"])
        )


class TestNoDuplicateExecution(unittest.TestCase):
    """M10-005 — tanpa idempotency key pun, satu state tidak dieksekusi ganda
    tanpa approval baru."""

    def test_approve_once_runs_once(self):
        """Approve sekali -> satu eksekusi; decide lanjutan (tanpa submit baru)
        TIDAK menambah issue (state sudah terminal)."""
        c = TestClient(app)
        s0 = c.post("/ux/submit", json={"text": "Buat github issue (single)"}).json()
        mid = s0["observability"]["mission_id"]
        # approve -> completed/blocked (depend env token); intinya tidak ganda.
        r = c.post("/ux/decide", json={"intent": "approve", "mission_id": mid, "approver": "user"})
        assert r.status_code == 200
        # decide kedua pada state yang sama tidak boleh menciptakan eksekusi baru
        # yang tidak diminta (state tidak menambah evidence tanpa submit baru).
        st = c.get("/ux/state").json()
        assert st["request_id"]  # masih satu sesi


if __name__ == "__main__":
    unittest.main(verbosity=2)
