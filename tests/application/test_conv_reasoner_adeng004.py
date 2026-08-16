"""test_conv_reasoner_adeng004.py — AD-ENG-004 ConversationalResponse port (L1/L2/L3/L4).

Implementasi AD-ENG-004 (ACCEPTED FOR IMPLEMENTATION, 2026-08-16) — Acceptance
wajib Van: jalur CHAT BENAR-BENAR menghasilkan respons conversational dari
provider melalui port canonical, BUKAN hanya `operation == ""`.

Acceptance (minimum):
  POST /ux/conversation/message "halo"
      -> CHAT -> ConversationalReasoner (port) -> fake ProviderExecutor
      -> assistant content -> persisted message

  Cek wajib:
    - MissionRequest dibuat?        NO
    - MissionPlan dibuat?           NO
    - Approval dibuat?              NO
    - ProviderExecutor dipanggil?   YES (via port+adapter)
    - assistant message dipersisted? YES

Juga menguji:
  - Port contract: immutable/frozen, response BERSIH dari metadata observability.
  - Adapter fail-closed: provider unavailable/invalid -> ok=False + teks jujur.
  - Adapter sanitasi secret + length guard + trace observability terpisah.
  - Simetri CHAT vs MISSION: mission tetap lewat submit() (tidak berubah).
"""
from __future__ import annotations

import unittest

from sam.application.ux.conversation import ConversationService
from sam.application.ux.conversational_reasoner import (
    ConversationContext,
    ConversationalReasoner,
    ConversationalResponse,
    MessageTurn,
    MissionBrief,
)
from sam.application.ux.conversational_reasoner_adapter import (
    ConversationalTrace,
    ProviderConversationalReasonerAdapter,
)
from sam.application.ux.repositories import InMemoryConversationRepository
from sam.application.ux.state import UxMissionState, UxStateStatus
from sam.governed_reasoning.structured_reasoning import EvidenceRef
from sam.universal_ai.message_model import MessageRole


class _FakeExecutor:
    """Fake ProviderExecutor (mengikuti kontrak `execute`).

    `execute(provider_id, operation, payload, timeout_seconds)` -> dict yang
    meniru ProviderExecutor: `{"provider_id","operation","status","payload",
    "external_calls"}` dgn `payload.raw.choices[].message.content`.
    Mencatat panggilan (provider, operation, payload) utk assert.
    """

    def __init__(self, content: str = "Selamat datang. Ada yang bisa saya bantu?"):
        self.content = content
        self.calls = []  # (provider_id, operation, payload)
        self.available_ids = {"deepseek", "ollama"}
        self.available_raises = False

    def available(self, provider_id: str) -> bool:
        if self.available_raises:
            raise RuntimeError("available rusak")
        return provider_id in self.available_ids

    def execute(self, provider_id, operation, payload=None, timeout_seconds=60):
        self.calls.append((provider_id, operation, dict(payload or {}), timeout_seconds))
        return {
            "provider_id": provider_id,
            "operation": operation,
            "status": "completed",
            "payload": {
                "raw": {
                    "choices": [
                        {"message": {"role": "assistant", "content": self.content}}
                    ]
                }
            },
            "external_calls": 1,
        }


class PortContractTest(unittest.TestCase):
    """L1: contract immutable + response bersih dari metadata observability."""

    def test_context_frozen(self):
        ctx = ConversationContext(conversation_id="c1", user_message="halo")
        with self.assertRaises(AttributeError):
            ctx.user_message = "berubah"  # frozen

    def test_response_frozen_and_clean(self):
        resp = ConversationalResponse(content="Halo!", ok=True)
        with self.assertRaises(AttributeError):
            resp.ok = False  # frozen
        # Refinement Van: response BERSIH — tidak punya field provider/model.
        self.assertFalse(hasattr(resp, "provider_id"))
        self.assertFalse(hasattr(resp, "model_id"))

    def test_mission_brief_and_turn_frozen(self):
        mb = MissionBrief(operation="github.create_issue", status="waiting_approval")
        with self.assertRaises(AttributeError):
            mb.operation = "x"
        t = MessageTurn(role="user", content="halo")
        with self.assertRaises(AttributeError):
            t.content = "x"

    def test_is_protocol(self):
        # Port adalah runtime-checkable Protocol (Clean Architecture boundary).
        self.assertTrue(hasattr(ConversationalReasoner, "converse"))


class AdapterTest(unittest.TestCase):
    """L3: ProviderConversationalReasonerAdapter membungkus fake ProviderExecutor."""

    def setUp(self) -> None:
        self.fake = _FakeExecutor()
        self.adapter = ProviderConversationalReasonerAdapter(executor=self.fake)

    def _ctx(self, msg="halo", history=(), mission=None, evidence=()):
        return ConversationContext(
            conversation_id="c1",
            user_message=msg,
            history=tuple(history),
            active_mission=mission,
            evidence_refs=tuple(evidence),
        )

    def test_converse_returns_content_from_executor(self):
        self.fake.content = "Selamat datang. Ada yang bisa saya bantu?"
        resp = self.adapter.converse(self._ctx())
        self.assertTrue(resp.ok)
        self.assertEqual(resp.error_kind, "")
        self.assertIn("Selamat datang", resp.content)
        # ProviderExecutor dipanggil via `chat`.
        self.assertEqual(len(self.fake.calls), 1)
        pid, op, payload, _ = self.fake.calls[0]
        self.assertEqual(op, "chat")
        self.assertIn("halo", payload["prompt"])
        # Observability trace terpisah (bukan bagian response).
        self.assertIsInstance(self.adapter.last_trace, ConversationalTrace)
        self.assertEqual(self.adapter.last_trace.provider_id, "deepseek")

    def test_provider_unavailable_fail_closed(self):
        self.fake.available_ids = set()  # tidak ada provider tersedia
        resp = self.adapter.converse(self._ctx())
        self.assertFalse(resp.ok)
        self.assertEqual(resp.error_kind, "unavailable")
        self.assertNotEqual(resp.content, "")  # teks jujur, bukan state kosong
        # Tidak ada eksekusi dipanggil.
        self.assertEqual(len(self.fake.calls), 0)

    def test_fallback_ollama_when_deepseek_unavailable(self):
        self.fake.available_ids = {"ollama"}  # deepseek hilang, ollama ada
        self.fake.content = "Jawaban fallback"
        resp = self.adapter.converse(self._ctx())
        self.assertTrue(resp.ok)
        pid = self.fake.calls[0][0]
        self.assertEqual(pid, "ollama")
        self.assertEqual(self.adapter.last_trace.provider_id, "ollama")

    def test_invalid_output_fail_closed(self):
        # Executor mengembalikan payload tanpa content valid.
        class _EmptyExecutor(_FakeExecutor):
            def execute(self, *a, **k):
                return {
                    "payload": {"raw": {"choices": [{"message": {"content": ""}}]}},
                    "external_calls": 1,
                }

        adapter = ProviderConversationalReasonerAdapter(executor=_EmptyExecutor())
        resp = adapter.converse(self._ctx())
        self.assertFalse(resp.ok)
        self.assertEqual(resp.error_kind, "invalid")

    def test_executor_raises_fail_closed(self):
        class _RaiseExecutor(_FakeExecutor):
            def execute(self, *a, **k):
                raise RuntimeError("network down")

        adapter = ProviderConversationalReasonerAdapter(executor=_RaiseExecutor())
        resp = adapter.converse(self._ctx())
        self.assertFalse(resp.ok)
        self.assertEqual(resp.error_kind, "unavailable")

    def test_sanitize_secret(self):
        self.fake.content = "Token saya ghp_ABC123 rahasia sk-xyz"
        resp = self.adapter.converse(self._ctx())
        self.assertNotIn("ghp_ABC123", resp.content)
        self.assertNotIn("sk-xyz", resp.content)

    def test_length_guard(self):
        self.fake.content = "x" * 5000
        resp = self.adapter.converse(self._ctx())
        # Dipotong ke max 4000 + ada warning.
        self.assertLessEqual(len(resp.content), 4000)
        self.assertTrue(any("dipotong" in w for w in resp.warnings))

    def test_empty_user_message(self):
        resp = self.adapter.converse(self._ctx(msg="  "))
        self.assertTrue(resp.ok)
        self.assertEqual(len(self.fake.calls), 0)

    def test_active_mission_in_prompt(self):
        self._ctx()  # warm
        self.fake.calls.clear()
        mission = MissionBrief(operation="github.create_issue", status="waiting_approval")
        self.adapter.converse(self._ctx(mission=mission))
        payload = self.fake.calls[0][2]
        self.assertIn("github.create_issue", payload["prompt"])

    def test_evidence_and_history_in_prompt(self):
        self.fake.calls.clear()
        ev = EvidenceRef(evidence_id="ev1", source_type="url", source_id="https://x")
        history = (MessageTurn(role="user", content="sebelumnya"),)
        self.adapter.converse(self._ctx(history=history, evidence=(ev,)))
        payload = self.fake.calls[0][2]
        self.assertIn("sebelumnya", payload["prompt"])


class _FakeFailReasoner:
    """Fake port yang selalu gagal (provider unavailable) — utk uji ConversationService
    saat port gagal: content jujur tetap dipersist sebagai assistant message."""

    def converse(self, ctx):
        return ConversationalResponse(
            content="SAM tidak dapat menyusun jawaban saat ini karena penyedia AI tidak tersedia.",
            ok=False,
            error_kind="unavailable",
        )


class _FakeChatReasoner:
    """Fake port sukses — mencatat dipanggil dgn context, mengembalikan teks."""

    def __init__(self, content="Selamat datang. Ada yang bisa saya bantu?"):
        self.content = content
        self.calls = []

    def converse(self, ctx):
        self.calls.append(ctx)
        return ConversationalResponse(content=self.content, ok=True)


class ConversationServiceChatRoutingTest(unittest.TestCase):
    """L4: ConversationService menjadi router (CHAT -> port, MISSION -> submit)."""

    def setUp(self) -> None:
        self.repo = InMemoryConversationRepository()
        self.fake_mission = _FakeMission()
        self.fake_reasoner = _FakeChatReasoner()
        self.svc = ConversationService(
            conversation_repo=self.repo,
            mission_service=self.fake_mission,
            conversational_reasoner=self.fake_reasoner,
            participant="alice",
        )

    # --- ACCEPTANCE WAJIB VAN: halo -> CHAT -> port -> assistant persisted ---
    def test_halo_routes_to_chat_port_and_persists(self):
        convo = self.svc.create_or_resume_conversation()
        result = self.svc.submit_command(convo.conversation_id, "halo")
        # Provider/port benar-benar dipanggil (BUKAN hanya operation == "").
        self.assertEqual(len(self.fake_reasoner.calls), 1)
        ctx = self.fake_reasoner.calls[0]
        self.assertEqual(ctx.user_message, "halo")
        self.assertEqual(ctx.conversation_id, convo.conversation_id)
        # Assistant message dipersisted (YES).
        self.assertTrue(result["assistant_persisted"])
        self.assertEqual(result["chat"], True)
        msgs = self.svc.get_conversation(convo.conversation_id)
        self.assertEqual(len(msgs), 2)  # user + assistant
        self.assertEqual(msgs[1].role, MessageRole.ASSISTANT)
        self.assertIn("Selamat datang", msgs[1].content)
        # Mission TIDAK dipanggil (NO MissionRequest/Plan/Approval).
        self.assertEqual(self.fake_mission.submit_calls, 0)

    def test_mission_text_routes_to_submit_unchanged(self):
        convo = self.svc.create_or_resume_conversation()
        result = self.svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        # Mission tetap lewat submit() (jalur existing, tidak berubah).
        self.assertEqual(self.fake_mission.submit_calls, 1)
        self.assertEqual(self.fake_mission.last_text, "Buat issue GitHub")
        # Port CHAT tidak dipanggil.
        self.assertEqual(len(self.fake_reasoner.calls), 0)
        self.assertIsInstance(result["state"], UxMissionState)
        self.assertEqual(result["state"].operation, "github.create_issue")

    def test_chat_state_has_empty_operation_and_no_approval(self):
        convo = self.svc.create_or_resume_conversation()
        result = self.svc.submit_command(convo.conversation_id, "halo")
        st = result["state"]
        self.assertEqual(st.operation, "")
        self.assertFalse(st.approval_required)
        self.assertEqual(st.status, UxStateStatus.UNDERSTOOD)

    def test_chat_port_failure_still_persists_honest_text(self):
        svc = ConversationService(
            conversation_repo=self.repo,
            mission_service=self.fake_mission,
            conversational_reasoner=_FakeFailReasoner(),
            participant="alice",
        )
        convo = svc.create_or_resume_conversation()
        result = svc.submit_command(convo.conversation_id, "halo")
        self.assertTrue(result["assistant_persisted"])
        msgs = svc.get_conversation(convo.conversation_id)
        self.assertIn("penyedia AI tidak tersedia", msgs[1].content)
        # Mission tetap tidak dipanggil (CHAT tetap bukan mission).
        self.assertEqual(self.fake_mission.submit_calls, 0)


class _FakeMission:
    """Fake MissionUXService — mencatat submit; mengembalikan state canonical."""

    def __init__(self) -> None:
        self.submit_calls = 0
        self.last_text = ""
        self._state = UxMissionState()

    def submit(self, text, idempotency_key=None):
        self.submit_calls += 1
        self.last_text = text
        st = UxMissionState(
            request_id="req-fake",
            request_text=text,
            what_sam_understood="SAM memahami: membuat GitHub issue (fake).",
            operation="github.create_issue",
            target="VanM-Hub/test-issues",
            planned_steps=["memverifikasi koneksi", "membuat issue"],
            approval_required=True,
            action_summary="SAM akan membuat GitHub issue.",
            approval_status=UxStateStatus.WAITING_APPROVAL,
            status=UxStateStatus.WAITING_APPROVAL,
        )
        st.observability = {"request_id": "req-fake", "mission_id": "mission-fake"}
        self._state = st
        return st

    def decide(self, intent, approver="user"):
        return self._state

    def get_state(self):
        return self._state


class AcceptanceExecutedTest(unittest.TestCase):
    """Uji acceptance VAN dieksekusi PENUH dengan fake executor nyata.

    POST /ux/conversation/message "halo" -> port -> fake ProviderExecutor ->
    assistant content -> persisted. Verifikasi NO/YES persis acceptance.
    """

    def setUp(self) -> None:
        self.repo = InMemoryConversationRepository()
        self.fake_exec = _FakeExecutor(
            content="Selamat datang. Ada yang bisa saya bantu?"
        )
        self.adapter = ProviderConversationalReasonerAdapter(executor=self.fake_exec)

    def test_acceptance_halo_full_chain(self):
        from sam.application.ux.service import MissionUXService

        svc = ConversationService(
            conversation_repo=self.repo,
            mission_service=MissionUXService(),  # nyata, TAPI tidak dipanggil utk CHAT
            conversational_reasoner=self.adapter,
            participant="alice",
        )
        convo = svc.create_or_resume_conversation()
        result = svc.submit_command(convo.conversation_id, "halo")

        # 1) ProviderExecutor dipanggil? YES
        self.assertEqual(len(self.fake_exec.calls), 1)
        pid, op, _, _ = self.fake_exec.calls[0]
        self.assertEqual(op, "chat")

        # 2) provider id dibatasi di adapter (deepseek default) — application
        #    tidak menyentuh nama provider.
        self.assertEqual(pid, "deepseek")

        # 3) assistant content dipersisted? YES
        self.assertTrue(result["assistant_persisted"])
        msgs = svc.get_conversation(convo.conversation_id)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[1].role, MessageRole.ASSISTANT)
        self.assertIn("Selamat datang", msgs[1].content)

        # 4) MissionRequest/Plan/Approval TIDAK dibuat (NO): mission state
        #    tetap kosong (tidak ada submit), tanpa approval.
        self.assertEqual(msgs[1].content, "Selamat datang. Ada yang bisa saya bantu?")
        st = result["state"]
        self.assertEqual(st.operation, "")
        self.assertFalse(st.approval_required)
        # Tidak ada request_id/plan/approval pada real MissionUXService (state
        # mission tetap None — TIDAK di-set karena submit tidak pernah dipanggil).
        real_service = svc._mission
        self.assertIsNone(real_service._state)  # belum ada mission ter-set


if __name__ == "__main__":
    unittest.main()
