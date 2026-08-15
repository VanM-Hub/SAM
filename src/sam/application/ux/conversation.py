"""conversation.py — ConversationService (Sprint 2, S2-2).

ORCHESTRATOR conversation di application boundary. TIDAK executor, TIDAK
pemegang authority, TIDAK LLM.

Kontrak (sesuai keputusan Van / Opsi Y):
    Chat -> ConversationService -> MissionUXService -> canonical runtime

ConversationService:
  - create/resume conversation (ID stabil, resume bila ada).
  - append user Message (canonical `universal_ai.Message`, disimpan utuh).
  - menerima command user -> panggil `MissionUXService.submit()` (SATU pintu
    misi) -> ambil `UxMissionState` (state canonical) -> bangun assistant
    Message HANYA dari hasil/state nyata -> persist semuanya ke
    ConversationRepository.
  - approve/reject -> forwarding ke `MissionUXService.decide()` (REUSE
    ApprovalGate canonical existing; TIDAK membuat approval gate baru).

Larangan yang DIPATUHI (tidak pernah):
  - memanggil ProviderInvoker / ConversationAPI.send_message() (jalur LLM
    universal_ai TIDAK dipakai di sini).
  - membuat executor / menjalankan GitHub-HTTP-provider secara langsung.
  - membuat model ConversationMessage baru (pakai `universal_ai.Message`).
  - menambahkan mission_id/request_id ke Message universal.
  - membuat respons LLM palsu (konten assistant murni proyeksi state nyata).
  - membuat state lokal yang menggantikan UxMissionState (state canonical
    MILIK MissionUXService; ConversationService hanya membaca/proyeksinya).

Association conversation->mission TIDAK disimpan sbg store terpisah (audit S2-3):
state mission canonical MILIK MissionUXService & survive restart via
`_recover_from_store`; ConversationService membaca/proyeksinya saja, tanpa
menduplikasi sumber kebenaran (menghindari "persistence kedua" diam-diam).
"""
from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from sam.universal_ai.conversation_model import (
    Conversation,
    ConversationStatus,
)
from sam.universal_ai.conversation_session import (
    ConversationSession,
    SessionState,
)
from sam.universal_ai.message_model import Message, MessageRole

from sam.application.ux.repositories import ConversationRepository
from sam.application.ux.state import UxMissionState


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Proyeksi state canonical -> teks assistant yang JUJUR (bukan LLM).
# Semua nilai diambil dari field `UxMissionState` yg SUDAH di-sanitize
# (M10-002/M8-005: state tidak pernah memuat token/secret).
# ---------------------------------------------------------------------------
def _state_to_assistant_text(state: "UxMissionState") -> str:
    """Buat kalimat ringkas dari state mission nyata utk assistant message.

    TIDAK mengarang: hanya memproyeksikan field yg ada (understood, operation,
    planned_steps, approval, status, result, failure, evidence). Bila state
    kosong -> kalimat jujur "belum ada hasil" (bukan konten sintetis).
    """
    if state is None:
        return "SAM belum memiliki state mission untuk command ini."

    understood = (state.what_sam_understood or "").strip()
    operation = (state.operation or "").strip()
    planned = list(state.planned_steps or [])
    approval_status = (state.approval_status or "").strip()
    status = (state.status or "").strip()
    result_summary = (state.result_summary or "").strip()
    failure_message = (state.failure_message or "").strip()
    evidence = list(state.evidence or [])

    parts: List[str] = []
    if understood:
        parts.append(understood)
    if operation:
        parts.append(f"Operasi: {operation}")
    if planned:
        steps = "; ".join(f"{i+1}. {s}" for i, s in enumerate(planned))
        parts.append(f"Rencana: {steps}")
    if approval_status:
        parts.append(f"Persetujuan: {approval_status}")
    if status:
        parts.append(f"Status: {status}")
    if result_summary:
        parts.append(f"Hasil: {result_summary}")
    if failure_message:
        parts.append(f"Catatan: {failure_message}")
    if evidence:
        refs = "; ".join(
            e.get("url") or e.get("target") or e.get("detail") or str(e)
            for e in evidence
        )
        parts.append(f"Bukti: {refs}")

    if not parts:
        return "SAM tidak menemukan hasil nyata untuk command ini."
    return "\n".join(parts)


class ConversationService:
    """Orchestrator conversation di application boundary.

    Satu-satunya pintu: user kirim command -> persist Message -> MissionUXService
    -> state canonical -> proyeksi assistant -> persist. Eksekusi mission hanya
    terjadi di dalam `MissionUXService` (canonical runtime), TIDAK di sini.
    """

    def __init__(
        self,
        conversation_repo: Optional[ConversationRepository] = None,
        mission_service: Optional["object"] = None,
        participant: str = "user",
    ) -> None:
        """Wire repository conversation + MissionUXService.

        - conversation_repo: implementasi `ConversationRepository` (wajib;
          bisa InMemory utk dev/test, Postgres utk produksi). Bila None, dibuat
          InMemory (aman utk tes; produksi via endpoint meneruskan unit yg benar).
        - mission_service: instance `MissionUXService` (orchestrator misi canonical).
          Bila None, dibuat default `MissionUXService()` (tanpa persistence
          khusus -> perilaku in-memory default, aman & non-destruktif).
        - participant: identitas sisi user untuk conversation (default "user").
        """
        if conversation_repo is None:
            from sam.application.ux.repositories import (
                InMemoryConversationRepository,
            )

            conversation_repo = InMemoryConversationRepository()
        self._repo: ConversationRepository = conversation_repo
        if mission_service is None:
            from sam.application.ux.service import MissionUXService

            mission_service = MissionUXService()
        self._mission = mission_service
        self._participant = participant

    # ------------------------------------------------------------------
    # 1) create / resume conversation (ID stabil, resume bila ada)
    # ------------------------------------------------------------------
    def create_or_resume_conversation(self, participant: Optional[str] = None) -> Conversation:
        """Ambil conversation OPEN yang sudah ada untuk participant, atau buat baru.

        ID stabil: bila sudah ada conversation dengan status OPEN untuk
        participant yg sama, resume (kembalikan yg sama) -> acceptance
        "conversation ID stabil" & "resume" terpenuhi tanpa duplikasi.
        """
        participant = participant or self._participant
        existing = self._list_open_conversation(participant)
        if existing is not None:
            return existing
        convo = Conversation(
            conversation_id=f"conv-{uuid.uuid4().hex[:12]}",
            title="",
            participant=participant,
            status=ConversationStatus.OPEN,
            created_at=_now_utc(),
        )
        self._repo.save_conversation(convo)
        self._ensure_open_session(convo.conversation_id)
        return convo

    def _list_open_conversation(self, participant: str) -> Optional[Conversation]:
        """Balikan conversation OPEN pertama utk participant (resume)."""
        if not participant:
            return None
        for cid in self._repo.list_conversations():
            convo = self._repo.load_conversation(cid)
            if convo is None:
                continue
            if (
                convo.participant == participant
                and convo.status == ConversationStatus.OPEN
            ):
                return convo
        return None

    def _ensure_open_session(self, conversation_id: str) -> ConversationSession:
        """Ambil / buat session ACTIVE utk conversation (resume session)."""
        for sid in self._repo.list_sessions(conversation_id):
            sess = self._repo.load_session(sid)
            if sess is not None:
                if sess.state == SessionState.ACTIVE:
                    return sess
                # Session ada tapi tidak ACTIVE -> buat ACTIVE baru (resume).
                resumed = ConversationSession(
                    session_id=sid,
                    conversation_id=conversation_id,
                    state=SessionState.ACTIVE,
                    provider_id=sess.provider_id,
                    model_id=sess.model_id,
                    created_at=sess.created_at,
                )
                self._repo.save_session(resumed)
                return resumed
        session = ConversationSession(
            session_id=f"sess-{uuid.uuid4().hex[:12]}",
            conversation_id=conversation_id,
            state=SessionState.ACTIVE,
            created_at=_now_utc(),
        )
        self._repo.save_session(session)
        return session

    # ------------------------------------------------------------------
    # 2) append user Message (canonical, disimpan utuh)
    # ------------------------------------------------------------------
    def append_user_message(self, conversation_id: str, content: str) -> Message:
        """Tambah pesan USER kanonikal ke conversation & persist.

        Konversasi & session dipastikan ada (auto-create jika belum). User
        message tersimpan UTUH (`universal_ai.Message`) — membership field
        (role USER) + content + conversation/session ref, tanpa secret.
        """
        self._ensure_conversation(conversation_id)
        session = self._ensure_open_session(conversation_id)
        msg = Message(
            message_id=f"msg-{uuid.uuid4().hex[:12]}",
            role=MessageRole.USER,
            content=content,
            conversation_id=conversation_id,
            session_id=session.session_id,
            evidence_refs=(),
            created_at=_now_utc(),
        )
        self._repo.append_message(msg)
        return msg

    def _ensure_conversation(self, conversation_id: str) -> None:
        convo = self._repo.load_conversation(conversation_id)
        if convo is None:
            raise KeyError(
                f"conversation `{conversation_id}` tidak ditemukan — "
                "buat dulu via create_or_resume_conversation()."
            )

    # ------------------------------------------------------------------
    # 3) submit command -> MissionUXService -> state canonical -> assistant
    # ------------------------------------------------------------------
    def submit_command(
        self,
        conversation_id: str,
        text: str,
        idempotency_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Terima command user; orkestrasi ke MissionUXService; proyeksi assistant.

        Flow (orde ketat, kegagalan persist TIDAK diklaim sukses):
          1. persist user Message (gagal -> raise, 0 klaim sukses).
          2. panggil `MissionUXService.submit(text)` -> `UxMissionState`
             (state canonical; orchestrator misi).
          3. bangun assistant Message HANYA dari field state nyata.
          4. persist assistant Message (gagal -> state mission tetap terjadi,
             tapi dikembalikan penanda `assistant_persisted=False` jujur,
             BUKAN klaim sukses).

        Returns dict:
            {
              "state": UxMissionState (canonical, dari MissionUXService),
              "conversation_id": str,
              "user_message_id": str,
              "assistant_message_id": str,
              "assistant_persisted": bool,
            }
        """
        # 1) Persist user message TERLEBIH DAHULU (harus tersimpan sebelum apa pun).
        user_msg = self.append_user_message(conversation_id=conversation_id, content=text)

        # 2) Orkestrasi ke MissionUXService -> state canonical.
        #    (Keputusan audit S2-3: TIDAK ada assosiasi `_mission_link` RAM.
        #    State mission canonical MILIK MissionUXService & survive restart via
        #    `_recover_from_store`; conversation tidak menyimpan duplikat sumber
        #    kebenaran mission agar tidak jadi "persistence kedua" diam-diam.)
        state = self._mission.submit(text=text, idempotency_key=idempotency_key)

        # 3) Bangun assistant text dari state NYATA (bukan LLM).
        assistant_content = _state_to_assistant_text(state)
        session = self._ensure_open_session(conversation_id)
        assistant_msg = Message(
            message_id=f"msg-{uuid.uuid4().hex[:12]}",
            role=MessageRole.ASSISTANT,
            content=assistant_content,
            conversation_id=conversation_id,
            session_id=session.session_id,
            evidence_refs=tuple(
                e.get("url") or e.get("target") or e.get("detail") or ""
                for e in (state.evidence or [])
            ),
            created_at=_now_utc(),
        )

        # 4) Persist assistant message. Bila gagal, JANGAN klaim sukses.
        assistant_persisted = True
        try:
            self._repo.append_message(assistant_msg)
        except Exception:
            assistant_persisted = False

        return {
            "state": state,
            "conversation_id": conversation_id,
            "user_message_id": user_msg.message_id,
            "assistant_message_id": assistant_msg.message_id,
            "assistant_persisted": assistant_persisted,
        }

    # ------------------------------------------------------------------
    # 4) approve / reject — REUSE ApprovalGate canonical (MissionUXService.decide)
    # ------------------------------------------------------------------
    def decide(
        self,
        intent: str,
        approver: str = "user",
    ) -> UxMissionState:
        """Forward keputusan ke ApprovalGate canonical SUDUT ADA (MissionUXService).

        ConversationService TIDAK membuat approval gate baru; ini hanyalah
        proxy yang memakai `MissionUXService.decide(intent, approver)` — gate
        eksekusi canonical yg sama (M9-003, sudah PROVEN).
        `intent` = "approve" | "reject" (dipetakan ke ApprovalDecisionIntent).
        """
        from sam.application.ux.approval import ApprovalDecisionIntent

        _intent = (
            ApprovalDecisionIntent.APPROVE
            if str(intent).lower() in ("approve", "approved", "yes")
            else ApprovalDecisionIntent.REJECT
        )
        return self._mission.decide(_intent, approver=approver)

    # ------------------------------------------------------------------
    # 5) baca conversation (messages) + navigasi
    # ------------------------------------------------------------------
    def get_conversation(self, conversation_id: str) -> List[Message]:
        """Balikan daftar Message utuh utk conversation (urut penambahan)."""
        return list(self._repo.list_messages(conversation_id))

    def conversation_exists(self, conversation_id: str) -> bool:
        """True bila conversation header sudah ada (fail-closed di route:
        conversation yg TIDAK dikenal -> 404, BUKAN dibuat diam-diam)."""
        try:
            return self._repo.load_conversation(conversation_id) is not None
        except Exception:  # noqa: BLE001 — tidak dikenal = False (fail-closed)
            return False

    def get_conversation_header(self, conversation_id: str) -> Optional[Conversation]:
        """Header conversation (BUKAN messages). None bila tidak ada."""
        return self._repo.load_conversation(conversation_id)

    def get_messages(self, conversation_id: str) -> List[Message]:
        """Alias readable utk get_conversation (pesan berurutan)."""
        return self.get_conversation(conversation_id)

    def list_conversations(self) -> List[str]:
        return list(self._repo.list_conversations())

    def get_mission_state(self, conversation_id: Optional[str] = None) -> Optional[UxMissionState]:
        """State canonical mission utk conversation (via MissionUXService).

        BUKAN state lokal pengganti — hanya pembaca dari `MissionUXService`.
        `conversation_id` opsional: ditembuskan sbg konteks, namun state
        canonical tetap milik MissionUXService (SATU state mission aktif).
        """
        return self._mission.get_state()
