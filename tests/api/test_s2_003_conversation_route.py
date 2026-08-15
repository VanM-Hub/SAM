"""test_s2_003_conversation_route.py — HTTP Conversation Boundary (Sprint 2, S2-3).

Acceptance S2-3 (kontrak Van) — dibuktikan dengan test nyata (bukan HTTP 200 saja):

  A. POST /ux/conversation/message membuat/resume conversation.
  B. User message benar-benar persisted.
  C. MissionUXService.submit() benar-benar terpanggil.
  D. Response berasal dari UxMissionState.
  E. GET setelah POST mengembalikan conversation yang sama.
  F. Restart service (repo sama) + GET tetap menemukan conversation.
  G. waiting_approval tidak mengeksekusi.
  H. POST /ux/decide (via ConversationService.decide) memakai MissionUXService.decide().
  I. Reject menghasilkan REJECTED dan zero mutation.
  J. Tidak ada ProviderInvoker di route.
  K. Tidak ada executor di route.
  L. Credential tidak masuk response.
  M. Error persistence tidak dilaporkan sebagai successful conversation.
  N. Malformed request -> validation error, bukan mission execution.
  O. Conversation ID tidak dikenal -> fail-closed (404), bukan create diam-diam.
  P. Dua request berbeda tidak saling mencampur conversation.

Isolasi: test meng-inject `_routes.conversations` dengan ConversationService
(repo InMemory segar PER-TEST + mission stub) sehingga TIDAK menyentuh
`_routes.service` mission global yang dipakai test ux lain (anti test pollution).
"""
from __future__ import annotations

import inspect
import unittest

from fastapi.testclient import TestClient

from sam.api.routes import ux as ux_routes
from sam.api.server import app
from sam.application.ux.conversation import ConversationService
from sam.application.ux.repositories import InMemoryConversationRepository
from sam.application.ux.state import UxMissionState, UxStateStatus


class _StubMission:
    """Stub MissionUXService utk isolasi route (TIDAK mengeksekusi apapun).

    Mencatat `submit` & `decide` dipanggil; status mission tiruan. Ini
    PENGGANTI MissionUXService di `ConversationService` — route tetap memanggil
    ConversationService -> stub ini (pintu orchestrasi yang SAMA). Bukan
    executor kedua: stub tidak menjalankan GitHub/provider apapun.
    """

    def __init__(self) -> None:
        self.submit_calls = 0
        self.decide_calls = 0
        self.last_text = ""
        self._state = UxMissionState()
        self._gate_called = False

    def submit(self, text: str, idempotency_key=None):
        self.submit_calls += 1
        self.last_text = text
        st = UxMissionState(
            request_id="req-s2-3",
            request_text=text,
            what_sam_understood="SAM memahami: membuat GitHub issue (stub S2-3).",
            operation="github.create_issue",
            target="VanM-Hub/test-issues",
            planned_steps=["memverifikasi koneksi", "membuat issue"],
            approval_required=True,
            action_summary="SAM akan membuat GitHub issue.",
            approval_status=UxStateStatus.WAITING_APPROVAL,
            status=UxStateStatus.WAITING_APPROVAL,
        )
        st.observability = {
            "request_id": "req-s2-3",
            "mission_id": "mission-s2-3",
            "status": UxStateStatus.WAITING_APPROVAL,
        }
        self._state = st
        return st

    def decide(self, intent, approver="user"):
        self.decide_calls += 1
        self._gate_called = True
        st = self._state
        raw = getattr(intent, "value", intent)
        if str(raw).lower() in ("approve", "approved", "yes"):
            st.approval_status = UxStateStatus.APPROVED
            st.status = UxStateStatus.APPROVED
        else:
            st.approval_status = UxStateStatus.REJECTED
            st.status = UxStateStatus.REJECTED
        return st

    def get_state(self):
        return self._state


class ConversationRouteTest(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)
        # Inject ConversationService segar (repo + stub mission) PER-TEST utk
        # isolasi; TIDAK mengubah `_routes.service` (mission global) milik test lain.
        self._orig_conversations = ux_routes._routes.conversations
        self.repo = InMemoryConversationRepository()
        self.stub = _StubMission()
        ux_routes._routes.conversations = ConversationService(
            conversation_repo=self.repo,
            mission_service=self.stub,
        )

    def tearDown(self) -> None:
        # Kembalikan ConversationService asli agar tidak mencemari test lain.
        ux_routes._routes.conversations = self._orig_conversations

    # --- A/B/C/D: POST membuat conversation, message persisted, submit terpanggil,
    #     response dari UxMissionState canonical ---
    def test_post_creates_conversation_and_persists(self):
        r = self.client.post(
            "/ux/conversation/message",
            json={"text": "Buat GitHub issue 'conversation'".lower()},
        )
        self.assertEqual(r.status_code, 200)
        body = r.json()
        cid = body["conversation_id"]
        self.assertTrue(cid.startswith("conv-"))
        # B: user message persisted
        self.assertEqual(len(body["messages"]), 2)  # user + assistant
        self.assertEqual(body["messages"][0]["role"], "user")
        self.assertEqual(body["messages"][1]["role"], "assistant")
        # C: MissionUXService.submit benar2 terpanggil (lewat ConversationService)
        self.assertEqual(self.stub.submit_calls, 1)
        # D: mission_state berasal dari UxMissionState (canonical)
        self.assertIsNotNone(body["mission_state"])
        self.assertEqual(body["mission_state"]["execution"]["status"], "waiting_approval")

    # --- A (resume): POST kedua tanpa conversation_id -> conversation SAMA ---
    def test_post_resumes_same_conversation(self):
        r1 = self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'dua'"}
        )
        cid1 = r1.json()["conversation_id"]
        r2 = self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'lanjut'"}
        )
        cid2 = r2.json()["conversation_id"]
        self.assertEqual(cid1, cid2, "conversation harus RESUME, bukan bikin baru")
        # messages bertambah: 4 (2+2)
        self.assertEqual(len(r2.json()["messages"]), 4)

    # --- E: GET setelah POST mengembalikan conversation yang sama ---
    def test_get_after_post_returns_same_conversation(self):
        r = self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'get'"}
        )
        cid = r.json()["conversation_id"]
        g = self.client.get(f"/ux/conversation/{cid}")
        self.assertEqual(g.status_code, 200)
        gb = g.json()
        self.assertEqual(gb["conversation_id"], cid)
        self.assertEqual(len(gb["messages"]), 2)
        self.assertEqual(gb["messages"][0]["role"], "user")

    # --- F: restart (repo sama) + GET tetap menemukan conversation ---
    def test_restart_keeps_conversation_findable(self):
        r = self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'restart'"}
        )
        cid = r.json()["conversation_id"]
        # Simulasikan restart: service BARU dengan repo SAMA (persistence dibagi).
        svc2 = ConversationService(
            conversation_repo=self.repo,
            mission_service=_StubMission(),
        )
        ux_routes._routes.conversations = svc2
        g = self.client.get(f"/ux/conversation/{cid}")
        self.assertEqual(g.status_code, 200)
        self.assertEqual(g.json()["conversation_id"], cid)
        self.assertEqual(len(g.json()["messages"]), 2)

    # --- G: waiting_approval TIDAK mengeksekusi (no evidence, 0 side effect) ---
    def test_waiting_approval_no_execution(self):
        r = self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'wait'"}
        )
        body = r.json()
        self.assertEqual(body["mission_state"]["execution"]["status"], "waiting_approval")
        self.assertEqual(body["mission_state"]["evidence"], [])

    # --- H: decide memakai MissionUXService.decide (reuse gate existing) ---
    def test_decide_reuses_mission_gate(self):
        r = self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'apr'"}
        )
        cid = r.json()["conversation_id"]
        st = ux_routes._routes.conversations.decide("approve", approver="user")
        self.assertTrue(self.stub._gate_called, "decide harus memanggil gate mission")
        self.assertEqual(st.approval_status, UxStateStatus.APPROVED)
        self.assertEqual(st.status, UxStateStatus.APPROVED)

    # --- I: reject -> REJECTED, zero mutation ---
    def test_reject_zero_mutation(self):
        self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'rej'"}
        )
        st = ux_routes._routes.conversations.decide("reject", approver="user")
        self.assertEqual(st.status, UxStateStatus.REJECTED)
        self.assertEqual(st.approval_status, UxStateStatus.REJECTED)
        self.assertEqual(st.evidence, [])  # tidak ada side effect / eksekusi

    # --- J/K: route tidak memanggil ProviderInvoker / executor / connector ---
    def test_route_no_provider_or_executor(self):
        # Ambil source TANPA docstring (agar penjelasan istilah di komentar
        # tidak memicu false-positive). Yang dicek: import & pemanggilan nyata.
        src = inspect.getsource(ux_routes)
        code = src.split('"""')[-1]  # bagian setelah docstring penutup
        self.assertNotIn("ProviderInvoker", code)
        self.assertNotIn("ConversationAPI", code)
        self.assertNotIn("ProviderExecutor", code)
        self.assertNotIn("run_mission(", code)
        # import blok kode route tidak menarik jalur eksekusi langsung:
        import re
        imports = "\n".join(re.findall(r"^from\s+\S+|^import\s+\S+", code, re.M))
        self.assertNotIn("execution_runtime", imports)
        self.assertNotIn("universal_ai.conversation_api", imports)
        self.assertNotIn("providers", imports)

    # --- L: credential tidak masuk response ---
    def test_credential_not_in_response(self):
        import os

        saved = os.environ.get("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = "ghp_SUPER_SECRET_TEST_TOKEN_123"
        try:
            r = self.client.post(
                "/ux/conversation/message",
                json={"text": "Buat GitHub issue 'cred'"},
            )
        finally:
            if saved is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = saved
        blob = str(r.json()).lower()
        self.assertNotIn("ghp_", blob)
        self.assertNotIn("super_secret_test_token", blob)

    # --- M: error persistence tidak dilaporkan sebagai successful conversation ---
    def test_persistence_error_not_reported_success(self):
        from sam.universal_ai.message_model import Message, MessageRole

        class _BrokenOnAssistant(InMemoryConversationRepository):
            def append_message(self, msg: Message) -> None:
                if msg.role == MessageRole.ASSISTANT:
                    raise RuntimeError("db down saat persist assistant")
                super().append_message(msg)

        repo = _BrokenOnAssistant()
        stub = _StubMission()
        ux_routes._routes.conversations = ConversationService(
            conversation_repo=repo, mission_service=stub
        )
        r = self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'persist'"}
        )
        self.assertEqual(r.status_code, 200)  # mission berjalan (state canonical)
        body = r.json()
        # JANGAN diklaim sukses bila persist assistant gagal:
        self.assertFalse(body["assistant_persisted"])
        # hanya user message yang tersimpan (assistant gagal)
        self.assertEqual(len(body["messages"]), 1)
        self.assertEqual(body["messages"][0]["role"], "user")
        # mission state tetap tersedia jujur (bukan fake success conversation)
        self.assertIsNotNone(body["mission_state"])

    # --- N: malformed -> validation error, NOT mission execution ---
    def test_malformed_text_is_validation_error(self):
        r = self.client.post(
            "/ux/conversation/message", json={"text": "   "}
        )
        # text kosong -> 422, submit TIDAK terpanggil (0 mission)
        self.assertEqual(r.status_code, 422)
        self.assertEqual(self.stub.submit_calls, 0)
        # get dengan text kosong tidak membuat conversation diam-diam
        self.assertEqual(len(self.repo.list_conversations()), 0)

    # --- O: conversation ID tidak dikenal -> 404 fail-closed ---
    def test_unknown_conversation_id_fail_closed(self):
        r_post = self.client.post(
            "/ux/conversation/message",
            json={"text": "Buat GitHub issue 'x'", "conversation_id": "conv-does-not-exist"},
        )
        self.assertEqual(r_post.status_code, 404)
        # tidak membuat conversation diam-diam
        self.assertEqual(len(self.repo.list_conversations()), 0)
        r_get = self.client.get("/ux/conversation/conv-does-not-exist")
        self.assertEqual(r_get.status_code, 404)

    # --- P: dua conversation berbeda tidak saling campur ---
    def test_two_conversations_isolated(self):
        # Buat dua conversation berbeda secara eksplisit (via repo langsung) lalu
        # kirim command ke masing2 -> messages TIDAK tercampur.
        cid_a = self.client.post(
            "/ux/conversation/message", json={"text": "Buat GitHub issue 'A'"}
        ).json()["conversation_id"]
        # conversation B terpisah: buat lewat service dengan participant beda.
        svc_b = ConversationService(
            conversation_repo=self.repo,
            mission_service=_StubMission(),
            participant="bob",
        )
        convo_b = svc_b.create_or_resume_conversation()
        self.client.post(
            "/ux/conversation/message",
            json={"text": "Buat GitHub issue 'B'", "conversation_id": convo_b.conversation_id},
        )
        # A hanya punya pesan A (bukan pesan B)
        ga = self.client.get(f"/ux/conversation/{cid_a}").json()
        self.assertEqual(len(ga["messages"]), 2)
        user_contents = [
            m["content"] for m in ga["messages"] if m["role"] == "user"
        ]
        self.assertTrue(any("A" in c for c in user_contents))
        self.assertFalse(
            any("npm " in c or "'B'" in c or "issue B" in c for c in user_contents),
            "conversation A bocor membawa content conversation B",
        )
        # conversation A tetap 2 pesan (tidak tercampur tambahan dari B)
        self.assertEqual(len(ga["messages"]), 2)


if __name__ == "__main__":
    unittest.main()
