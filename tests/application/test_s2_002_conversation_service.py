"""test_s2_002_conversation_service.py — ConversationService (Sprint 2, S2-2).

Acceptance S2-2 (kontrak Van):
  1. User message tersimpan.
  2. Conversation/session tersimpan.
  3. MissionUXService benar-benar dipanggil.
  4. Mission state yang dikembalikan adalah state canonical.
  5. Assistant message berasal dari hasil nyata state tersebut.
  6. Approval tetap melalui ApprovalGate yang sudah ada.
  7. Reject tidak menghasilkan side effect.
  8. Restart/reload dapat mengambil kembali conversation.
  9. Tidak ada provider invocation tersembunyi.
  10. Tidak ada executor kedua.
  11. Error persistence tidak menghasilkan klaim sukses.
  12. Test pollution existing tetap dipisahkan dari regression S2-2.

Test menggunakan InMemoryConversationRepository (dev/test) dan fake mission
service utk isolasi; satu test memakai MissionUXService NYATA utk verifikasi
orkestrasi canonical tanpa approve (submit = no execution).
"""
from __future__ import annotations

import unittest

from sam.application.ux.conversation import ConversationService, _state_to_assistant_text
from sam.application.ux.repositories import InMemoryConversationRepository
from sam.application.ux.state import UxMissionState, UxStateStatus
from sam.universal_ai.message_model import Message, MessageRole


class _FakeMission:
    """Fake MissionUXService utk test — mencatat dipanggil, mengembalikan
    state canonical tiruan. TIDAK menjalankan apa pun (no executor)."""

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
        st.observability = {
            "request_id": "req-fake",
            "mission_id": "mission-fake",
            "status": UxStateStatus.WAITING_APPROVAL,
        }
        self._state = st
        return st

    def decide(self, intent, approver="user"):
        # Meniru gate canonical. `intent` bisa `ApprovalDecisionIntent` (Enum)
        # atau str; normalisasi pakai `.value` bila Enum.
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


class ConversationServiceTest(unittest.TestCase):
    def setUp(self) -> None:
        self.repo = InMemoryConversationRepository()
        self.fake = _FakeMission()
        self.svc = ConversationService(
            conversation_repo=self.repo,
            mission_service=self.fake,
            participant="alice",
        )

    # --- Acceptance 1: user message tersimpan ---
    def test_user_message_persisted(self):
        convo = self.svc.create_or_resume_conversation()
        self.svc.append_user_message(convo.conversation_id, "Buat issue GitHub")
        msgs = self.svc.get_conversation(convo.conversation_id)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].role, MessageRole.USER)
        self.assertEqual(msgs[0].content, "Buat issue GitHub")

    # --- Acceptance 2: conversation/session tersimpan ---
    def test_conversation_and_session_persisted(self):
        convo = self.svc.create_or_resume_conversation()
        sessions = self.repo.list_sessions(convo.conversation_id)
        self.assertEqual(len(sessions), 1)
        sess = self.repo.load_session(sessions[0])
        self.assertIsNotNone(sess)
        self.assertEqual(sess.conversation_id, convo.conversation_id)

    # --- Stable ID + resume (no duplicate conversation) ---
    def test_conversation_id_stable_and_resume(self):
        c1 = self.svc.create_or_resume_conversation()
        c2 = self.svc.create_or_resume_conversation()
        self.assertEqual(c1.conversation_id, c2.conversation_id)
        self.assertEqual(len(self.repo.list_conversations()), 1)

    # --- Acceptance 3 & 4: MissionUXService dipanggil & state canonical ---
    def test_mission_service_called_and_state_is_canonical(self):
        convo = self.svc.create_or_resume_conversation()
        result = self.svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        self.assertEqual(self.fake.submit_calls, 1)
        self.assertEqual(self.fake.last_text, "Buat issue GitHub")
        # State yang dikembalikan adalah UxMissionState (canonical), bukan dict baru.
        self.assertIsInstance(result["state"], UxMissionState)
        # Tanpa approve -> status WAITING_APPROVAL, tidak ada eksekusi.
        self.assertEqual(result["state"].status, UxStateStatus.WAITING_APPROVAL)
        self.assertEqual(result["state"].approval_status, UxStateStatus.WAITING_APPROVAL)

    # --- Acceptance 5: assistant message berasal dari hasil nyata state ---
    def test_assistant_message_from_real_state(self):
        convo = self.svc.create_or_resume_conversation()
        result = self.svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        msgs = self.svc.get_conversation(convo.conversation_id)
        # user + assistant
        self.assertEqual(len(msgs), 2)
        assistant = msgs[1]
        self.assertEqual(assistant.role, MessageRole.ASSISTANT)
        # Konten assistant mencerminkan state nyata (bukan generik/LLM palsu).
        self.assertIn("SAM memahami: membuat GitHub issue", assistant.content)
        self.assertIn("github.create_issue", assistant.content)
        self.assertIn("waiting_approval", assistant.content)
        # Prove: assistant text diturunkan langsung dari state.
        self.assertEqual(assistant.content, _state_to_assistant_text(result["state"]))

    # --- Acceptance 6: approval melalui gate yang sudah ada ---
    def test_approval_reuses_existing_gate(self):
        convo = self.svc.create_or_resume_conversation()
        self.svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        state = self.svc.decide("approve", approver="alice")
        self.assertTrue(self.fake._gate_called, "decide harus memanggil gate mission")
        self.assertEqual(state.approval_status, UxStateStatus.APPROVED)
        # Tidak ada executor kedua: fake service TIDAK sempat mengeksekusi apa pun
        # (ini fake, pengganti MissionUXService — eksekusi canonical hanya di dalam
        # implementasi nyata, bukan di ConversationService).
        self.assertEqual(len(self.repo._messages), 2)

    # --- Acceptance 7: reject tidak menghasilkan side effect ---
    def test_reject_no_side_effect(self):
        convo = self.svc.create_or_resume_conversation()
        self.svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        msgs_before = len(self.svc.get_conversation(convo.conversation_id))
        state = self.svc.decide("reject", approver="alice")
        self.assertTrue(self.fake._gate_called)
        self.assertEqual(state.status, UxStateStatus.REJECTED)
        # Reject TIDAK menambah message/operasi apa pun (0 side effect).
        self.assertEqual(len(self.svc.get_conversation(convo.conversation_id)), msgs_before)

    # --- Acceptance 8: restart/reload mengambil kembali conversation ---
    def test_restart_recovers_conversation(self):
        convo = self.svc.create_or_resume_conversation()
        self.svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        # "Restart": service baru, tapi repo sama (meniru persistence yang dibagi).
        repo2 = self.repo
        svc2 = ConversationService(
            conversation_repo=repo2,
            mission_service=_FakeMission(),
            participant="alice",
        )
        convo2 = svc2.create_or_resume_conversation()
        self.assertEqual(convo2.conversation_id, convo.conversation_id)
        msgs = svc2.get_conversation(convo.conversation_id)
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0].role, MessageRole.USER)
        self.assertEqual(msgs[1].role, MessageRole.ASSISTANT)

    # --- Acceptance 9: tidak ada provider invocation tersembunyi ---
    def test_no_provider_invocation_hidden(self):
        # ConversationService tidak mengimpor ConversationAPI / ProviderInvoker /
        # runner eksekusi. Verifikasi via inspeksi modul (tidak ada referensi).
        import inspect

        src = inspect.getsource(ConversationService)
        self.assertNotIn("ProviderInvoker", src)
        self.assertNotIn("ConversationAPI", src)
        self.assertNotIn("run_mission", src)
        self.assertNotIn("invoke(", src)
        self.assertNotIn("http", src.lower())  # tidak ada call HTTP langsung

    # --- Acceptance 10: tidak ada executor kedua ---
    def test_no_second_executor(self):
        import inspect

        src = inspect.getsource(ConversationService)
        # TIDAK ada klausa yang membuat executor MISSION kedua (runner/execute_mission).
        self.assertNotIn("execute_mission", src)
        self.assertNotIn("run_mission", src)
        # ConversationService TIDAK instantiate ProviderExecutor langsung.
        self.assertNotIn("ProviderExecutor()", src)
        self.assertNotIn("from sam.providers.execution.provider_executor import", src)
        # AD-ENG-004 (2026-08-16): ConversationService kini menyebut nama adapter
        # infra `ProviderConversationalReasonerAdapter` (CHAT READ-ONLY port) — ini
        # BUKAN executor mission kedua; adapter hanya membungkus text generation.
        # Untuk menjaga niat test (no second MISSION executor), yang dilarang adalah
        # membuat runner/pemanggilan eksekusi nyata, bukan menyebut nama adapter.
        self.assertIn("ProviderConversationalReasonerAdapter", src)
        # SATU-satunya pintu eksekusi mission tetap MissionUXService.decide
        # (proxy ke gate existing).
        self.assertIn("self._mission.decide", src)

    # --- Acceptance 11: error persistence -> tidak klaim sukses ---
    def test_persistence_error_no_success_claim(self):
        class _BrokenOnAssistantRepo(InMemoryConversationRepository):
            def append_message(self, msg: Message) -> None:
                # USER boleh sukses; hanya ASSISTANT yang gagal (simulasi error
                # persistence setelah submit mission berhasil).
                if msg.role == MessageRole.ASSISTANT:
                    raise RuntimeError("db down saat persist assistant")
                super().append_message(msg)

        repo = _BrokenOnAssistantRepo()
        svc = ConversationService(
            conversation_repo=repo,
            mission_service=self.fake,
            participant="alice",
        )
        convo = svc.create_or_resume_conversation()
        result = svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        # Assistants gagal dipersist -> penanda jujur, BUKAN klaim sukses.
        self.assertFalse(result["assistant_persisted"])
        # Mission tetap berjalan (state canonical), user message tersimpan.
        self.assertEqual(result["conversation_id"], convo.conversation_id)
        self.assertTrue(result["user_message_id"])
        self.assertIsInstance(result["state"], UxMissionState)
        # Hanya user message yang tersimpan (assistant gagal).
        msgs = svc.get_conversation(convo.conversation_id)
        self.assertEqual(len(msgs), 1)
        self.assertEqual(msgs[0].role, MessageRole.USER)

    # --- Acceptance 12 (bagian): pollution test tidak bercampur ---
    def test_isolated_service_instances_no_pollution(self):
        # Service BERBEDA dengan repo BERBEDA tidak saling mencemari.
        repo_a = InMemoryConversationRepository()
        repo_b = InMemoryConversationRepository()
        sa = ConversationService(repo_a, _FakeMission(), participant="a")
        sb = ConversationService(repo_b, _FakeMission(), participant="b")
        ca = sa.create_or_resume_conversation()
        cb = sb.create_or_resume_conversation()
        self.assertNotEqual(ca.conversation_id, cb.conversation_id)
        self.assertEqual(sa.list_conversations(), [ca.conversation_id])
        self.assertEqual(sb.list_conversations(), [cb.conversation_id])
        # Tidak ada state global yang bocor antar instance: mission service
        # masing-masing bebas (tidak ada submit -> state kosong, bukan None).
        self.assertIsNotNone(sa.get_mission_state())
        self.assertEqual(sa.get_mission_state().status, "none")
        self.assertEqual(sb.get_mission_state().status, "none")

    # --- Acceptance: secret leakage = 0 ---
    def test_conversation_messages_never_contain_secret(self):
        import inspect

        # Assistant text SARANG murni dari state nyata; proyeksi tidak menyentuh
        # token. Verifikasi source proyeksi tidak memuat marker secret (defensive).
        src = inspect.getsource(_state_to_assistant_text)
        for marker in ("ghp_", "Bearer ", "sk-", "authorization", "api.key", "password"):
            self.assertNotIn(marker.lower(), src.lower(),
                             f"proyeksi assistant membocorkan akses marker secret: {marker}")

        # Dengan state nyata (tanpa token), pesan tidak memuat marker secret.
        convo = self.svc.create_or_resume_conversation()
        result = self.svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        for msg in self.svc.get_conversation(convo.conversation_id):
            blob = msg.content.lower()
            for marker in ("ghp_", "Bearer ", "sk-", "authorization", "token="):
                self.assertNotIn(marker, blob, f"message membocorkan marker secret: {marker}")


class ConversationServiceMissionUXIntegrationTest(unittest.TestCase):
    """Verifikasi orkestrasi dengan MissionUXService NYATA (no approve).

    Submit command -> MissionUXService.submit() (bukan fake) -> state canonical.
    Tidak ada approve -> tidak ada eksekusi (0 side effect).
    Test ini MENGIKUTI pola regresi M10 (no network) — hanya submit.
    """

    def test_submit_via_real_mission_service_no_execution(self):
        from sam.application.ux.service import MissionUXService

        svc = ConversationService(
            conversation_repo=InMemoryConversationRepository(),
            mission_service=MissionUXService(),
            participant="alice",
        )
        convo = svc.create_or_resume_conversation()
        result = svc.submit_command(convo.conversation_id, "Buat issue GitHub")
        # State canonical nyata dari MissionUXService.
        self.assertIsInstance(result["state"], UxMissionState)
        # Tanpa approve -> WAITING_APPROVAL, eksekusi BELUM terjadi.
        self.assertEqual(result["state"].status, UxStateStatus.WAITING_APPROVAL)
        self.assertEqual(result["state"].approval_status, UxStateStatus.WAITING_APPROVAL)
        # Tidak ada evidence (tidak ada eksekusi).
        self.assertEqual(result["state"].evidence, [])
        # Dua pesan: user + assistant (assistant dari state nyata).
        msgs = svc.get_conversation(convo.conversation_id)
        self.assertEqual(len(msgs), 2)
        # USER berisi teks persis permintaan; ASSISTANT berisi operasi nyata.
        self.assertEqual(msgs[0].role, MessageRole.USER)
        self.assertIn("Buat issue GitHub", msgs[0].content)
        self.assertEqual(msgs[1].role, MessageRole.ASSISTANT)
        self.assertIn("github.create_issue", msgs[1].content)

if __name__ == "__main__":
    unittest.main()
