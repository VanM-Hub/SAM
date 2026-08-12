"""Tests M9 UX REST Route adapter (/ux) — M9-002.

Memverifikasi jalur HTTP utuh untuk UI:
    HTML/UI -> POST /ux/submit -> MissionUXService -> state viewmodel
             -> POST /ux/decide -> ApprovalGate canonical -> status real

Route adalah adapter murni: tidak mengandung business logic, tidak bypass ke
GitHub/adapter, tidak membocorkan secret ke respons HTTP.
"""
from __future__ import annotations

import os
import unittest

from fastapi.testclient import TestClient

from sam.api.server import app


class UxRouteTest(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        # pastikan deterministik: tanpa token -> approve = BLOCKED (no side effect)
        self._saved_token = os.environ.get("GITHUB_TOKEN")
        os.environ.pop("GITHUB_TOKEN", None)

    def tearDown(self):
        if self._saved_token is not None:
            os.environ["GITHUB_TOKEN"] = self._saved_token
        else:
            os.environ.pop("GITHUB_TOKEN", None)

    def test_submit_returns_waiting_approval_state(self):
        r = self.client.post("/ux/submit", json={"text": "Buat GitHub issue 'uji route'"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["approval"]["status"], "waiting_approval")
        self.assertEqual(body["execution"]["status"], "waiting_approval")
        # bahasa manusia, bukan jargon internal MCR/provider
        self.assertIn("SAM memahami", body["understanding"]["what_sam_understood"])
        self.assertTrue(body["plan"]["approval_required"])

    def test_state_before_submit(self):
        r = self.client.get("/ux/state")
        self.assertEqual(r.status_code, 200)

    def test_decide_reject_marks_rejected(self):
        self.client.post("/ux/submit", json={"text": "Buat GitHub issue 'tolak route'"})
        r = self.client.post("/ux/decide", json={"intent": "reject", "approver": "user"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["approval"]["status"], "rejected")
        self.assertEqual(body["execution"]["status"], "rejected")
        self.assertEqual(body["execution"]["failure_kind"], "rejected")

    def test_decide_approve_without_token_is_blocked_not_fake(self):
        """Approve tanpa token -> BLOCKED, bukan fake success."""
        self.client.post("/ux/submit", json={"text": "Buat GitHub issue 'block route'"})
        r = self.client.post("/ux/decide", json={"intent": "approve", "approver": "user"})
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["execution"]["status"], "blocked")
        self.assertEqual(body["execution"]["failure_kind"], "blocked")
        self.assertIn("GITHUB_TOKEN", body["execution"]["failure_message"])

    def test_decide_invalid_intent_rejected(self):
        self.client.post("/ux/submit", json={"text": "Buat GitHub issue 'x'"})
        r = self.client.post("/ux/decide", json={"intent": "nonsense"})
        self.assertEqual(r.status_code, 200)
        self.assertIn("error", r.json())

    def test_http_response_never_leaks_secret(self):
        """Respons HTTP state tidak pernah memuat nilai/placeholder secret."""
        self.client.post("/ux/submit", json={"text": "Buat GitHub issue 'secret leak check'"})
        r = self.client.get("/ux/state")
        blob = r.text.lower()
        for marker in ("ghp_", "sk-", "bearer ", "authorization"):
            self.assertNotIn(marker, blob, f"HTTP response membocorkan {marker}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
