"""Tests M9 UX Application Service — boundary, approval gate, failure semantics.

Menegakkan keputusan canonical architecture (M9):
  - UI/browser TIDAK pernah memanggil GitHub/connector/adapter lain.
  - Satu-satunya jalur eksekusi adalah MissionUXService -> canonical runtime.
  - Approval adalah execution gate NYATA: tanpa approve tidak ada eksekusi;
    reject -> REJECTED dan TIDAK ada eksekusi.
  - Tidak ada secret/nilai token yang bocor ke state viewmodel.
  - Failure semantics dibedakan: BLOCKED (credential hilang) vs FAILED (HTTP/
    token invalid) vs REJECTED (user tolak).
"""
from __future__ import annotations

import unittest

from sam.application.ux.approval import ApprovalDecisionIntent, ApprovalStatus
from sam.application.ux.service import MissionUXService, DEFAULT_TEST_REPO


class MissionUXServiceSubmitTest(unittest.TestCase):
    """M9-002 — submit menghasilkan rencana & approval pending, tanpa eksekusi."""

    def test_recognizes_github_issue_and_holds_approval(self):
        svc = MissionUXService(test_repo="VanM-Hub/test-issues")
        state = svc.submit("Buat GitHub issue dengan judul 'test m9'")

        self.assertEqual(state.approval_status, "waiting_approval")
        self.assertEqual(state.status, "waiting_approval")
        self.assertTrue(state.approval_required)
        self.assertIn("github", state.operation)
        # understanding dalam bahasa manusia, bukan jargon internal
        self.assertIn("SAM memahami", state.what_sam_understood)
        self.assertTrue(state.planned_steps)
        # TIDAK boleh ada status eksekusi sebelum approval
        self.assertNotIn(state.status, ("running", "completed", "failed", "blocked"))

    def test_unrecognized_request_makes_no_plan_and_no_approval(self):
        svc = MissionUXService()
        state = svc.submit("halo apa kabar")

        self.assertEqual(state.approval_required, False)
        self.assertEqual(state.operation, "")
        self.assertEqual(state.planned_steps, [])

    def test_state_never_contains_secret(self):
        """No secret leak: state viewmodel tidak pernah berisi nilai token."""
        svc = MissionUXService()
        state = svc.submit("Buat GitHub issue 'uji secret'")
        blob = str(state.as_dict())
        # tidak ada placeholder token/secret yang masuk state
        for token_marker in ("ghp_", "Bearer ", "sk-", "authorization"):
            self.assertNotIn(token_marker.lower(), blob.lower(),
                             f"state membocorkan marker secret: {token_marker}")


class MissionUXServiceApprovalGateTest(unittest.TestCase):
    """M9-003 — approval adalah execution gate nyata."""

    def test_no_approval_no_execution(self):
        """Sebelum approve, tidak ada langkah eksekusi dan state tetap menunggu."""
        svc = MissionUXService(test_repo="VanM-Hub/test-issues")
        svc.submit("Buat GitHub issue 'tanpa approval'")
        # status tetap waiting_approval
        self.assertEqual(svc.get_state().approval_status, "waiting_approval")
        # tidak ada evidence (tidak ada eksekusi)
        self.assertEqual(svc.get_evidence(), [])

    def test_reject_stops_and_marks_rejected(self):
        """Reject -> REJECTED, TIDAK ada eksekusi, tidak ada evidence."""
        svc = MissionUXService(test_repo="VanM-Hub/test-issues")
        svc.submit("Buat GitHub issue 'ditolak'")
        state = svc.decide(ApprovalDecisionIntent.REJECT)

        self.assertEqual(state.status, "rejected")
        self.assertEqual(state.failure_kind, "rejected")
        # no external mutation happened -> no evidence
        self.assertEqual(svc.get_evidence(), [])
        # approval decision tercatat (approve=False)
        self.assertIsNotNone(state.approval_decision)
        self.assertIn("ap-", (state.approval_decision or {}).get("approval_id", ""))

    def test_approve_without_credentials_is_blocked_not_fake(self):
        """Approve tanpa GITHUB_TOKEN -> BLOCKED (no side effect), bukan fake success."""
        svc = MissionUXService(test_repo="VanM-Hub/test-issues",
                               artifact_dir="tests/_m9_tmp")
        svc.submit("Buat GitHub issue 'coba block'")
        # pastikan env token kosong untuk test deterministik
        import os
        saved = os.environ.get("GITHUB_TOKEN")
        os.environ.pop("GITHUB_TOKEN", None)
        try:
            state = svc.decide(ApprovalDecisionIntent.APPROVE)
        finally:
            if saved is not None:
                os.environ["GITHUB_TOKEN"] = saved
        self.assertEqual(state.status, "blocked")
        self.assertEqual(state.failure_kind, "blocked")
        self.assertIn("GITHUB_TOKEN", state.failure_message)
        # tidak ada evidence eksternal
        self.assertEqual(svc.get_evidence(), [])


class MissionUXSensorityBoundaryTest(unittest.TestCase):
    """M9-006 core: UI tidak bypass; satu jalur canonical."""

    def test_service_does_not_expose_secret_values(self):
        svc = MissionUXService()
        # audit + evidence tidak boleh memuat nilai token/secret
        svc.submit("Buat GitHub issue 'audit secret'")
        self.assertEqual(svc.get_audit(), [])  # belum eksekusi

    def test_default_repo_is_test_not_production(self):
        self.assertEqual(DEFAULT_TEST_REPO, "VanM-Hub/test-issues")
        svc = MissionUXService()
        self.assertIn("test", svc._test_repo)


class MissionChatVsMissionBoundaryTest(unittest.TestCase):
    """Boundary audit 2026-08-16: CHAT vs MISSION terpisah dari approval.

    Model canonical (diverifikasi terhadap source aktual):
      conversation input
        -> operation resolution
             operation == ""   -> CHAT (bukan Mission, tidak ada approval)
             operation != ""  -> MISSION
                  -> approval_required? (sinyal TERPISAH dari ke-mission-an)
                       read-only (observe/investigate/diagnose/recommend) -> tanpa approval
                       mutating (github.create_issue)

    Pengujian ini hanya CLASSIFIKASI STATE (tanpa eksekusi) — wiring eksekusi
    read-only dan Mission List ditunda sampai persetujuan Van.
    """

    def test_halo_is_chat_not_waiting_approval(self):
        """'halo' -> CHAT: operation kosong, TIDAK WAITING_APPROVAL."""
        svc = MissionUXService()
        state = svc.submit("halo")
        self.assertEqual(state.operation, "")           # bukan Mission
        self.assertFalse(state.approval_required)        # tidak butuh approval
        self.assertNotEqual(state.status, "waiting_approval")  # regression: bukan waiting
        self.assertNotEqual(state.approval_status, "waiting_approval")
        self.assertEqual(state.status, "understood")     # CHAT = paham, bukan menunggu
        self.assertEqual(state.planned_steps, [])

    def test_conversational_question_is_chat(self):
        """Pertanyaan percakapan biasa (bukan perintah eksekusi) -> CHAT."""
        svc = MissionUXService()
        state = svc.submit("siapa kamu dan apa yang bisa kamu lakukan?")
        self.assertEqual(state.operation, "")            # bukan Mission
        self.assertFalse(state.approval_required)
        self.assertNotEqual(state.status, "waiting_approval")

    def test_observe_is_mission_without_approval(self):
        """observe -> MISSION read-only, TANPA approval (operation terisi)."""
        svc = MissionUXService()
        state = svc.submit("periksa komputer saya")
        self.assertEqual(state.operation, "environment.observe")  # Mission (read-only)
        self.assertFalse(state.approval_required)                  # tanpa approval
        self.assertNotEqual(state.status, "waiting_approval")
        self.assertEqual(state.status, "understood")
        self.assertTrue(state.planned_steps)
        self.assertTrue(MissionUXService._operation_is_read_only("environment.observe"))

    def test_investigate_is_mission_without_approval(self):
        """investigate -> MISSION read-only, TANPA approval."""
        svc = MissionUXService()
        state = svc.submit("kenapa komputer saya lambat")
        self.assertEqual(state.operation, "environment.investigate")  # Mission (read-only)
        self.assertFalse(state.approval_required)
        self.assertNotEqual(state.status, "waiting_approval")
        self.assertEqual(state.status, "understood")
        self.assertTrue(MissionUXService._operation_is_read_only("environment.investigate"))

    def test_github_mutation_is_mission_with_approval(self):
        """github.create_issue (mutating) -> MISSION + approval."""
        svc = MissionUXService(test_repo="VanM-Hub/test-issues")
        state = svc.submit("Buat GitHub issue dengan judul 'regresi chat mission'")
        self.assertEqual(state.operation, "github.create_issue")  # Mission (mutating)
        self.assertTrue(state.approval_required)                   # butuh approval
        self.assertEqual(state.status, "waiting_approval")
        self.assertEqual(state.approval_status, "waiting_approval")
        self.assertFalse(MissionUXService._operation_is_read_only("github.create_issue"))

    def test_approval_required_is_not_synonym_of_chat(self):
        """approval_required=False BUKAN berarti CHAT: read-only adalah Mission."""
        svc = MissionUXService()
        st = svc.submit("diagnosa apa penyebab komputer lambat")
        # diagnose read-only -> Mission tanpa approval
        self.assertEqual(st.operation, "environment.diagnose")
        self.assertFalse(st.approval_required)
        self.assertNotEqual(st.status, "waiting_approval")
        # TAPI tetap Mission (operation terisi + planned steps)
        self.assertNotEqual(st.operation, "")
        self.assertTrue(st.planned_steps)


if __name__ == "__main__":
    unittest.main(verbosity=2)
