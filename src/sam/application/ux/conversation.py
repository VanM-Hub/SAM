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
from dataclasses import dataclass
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
from sam.application.ux.state import UxMissionState, UxStateStatus


def _now_utc() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# W3 — Koordinasi konfirmasi percakapan (bukan state machine mission baru).
#
# `CCPending` adalah KONTEKS PERCAKAPAN yang disimpan sementara oleh
# orchestrator conversation (wajar), BUKAN state mission / state machine baru
# (Van: jangan tambah state mission, jangan MissionCandidateService).
# Ia memuat proposal yang menunggu konfirmasi CHAT sebelum eksekusi canonical
# untuk observasi WARD eksternal (read-only).
# ---------------------------------------------------------------------------
@dataclass
class CCPending:
    """Proposal percakapan yang menunggu konfirmasi user (W3).

    Bukan ApprovalRequest / bukan mission state. Hanya konteks percakapan:
    teks asli user, operation/target hasil interpret, daftar kandidat Ward
    (bila ambiguous), dan tenant pemohon (utk ikat WardManager saat eksekusi).
    TIDAK pernah memuat secret/token.
    """

    text: str
    operation: str
    target: str
    understood: str
    ward_tenant: str = "user"
    candidates: tuple = ()  # tuple of (ward_id, name) bila ambiguous


# Kata jawaban konfirmasi percakapan (HANYA dipakai saat `_pending` ADA -
# bukan classifier semantic kedua; bukan deteksi intent mission).
_CONFIRM_WORDS = {
    "ya", "iya", "iyaa", "y", "yes", "lanjut", "lanjutkan", "oke", "ok",
    "okay", "setuju", "gas", "go", "true", "yakin", "boleh", "silahkan",
    "lanjut saja", "gass", "silakan", "ayok", "ayo", "siap", "jalankan",
}
_REJECT_WORDS = {
    "tidak", "nggak", "gak", "g", "no", "batal", "tunda", "nanti",
    "jangan", "stop", "cancel", "tidak jadi", "nggak jadi", "gajadi",
    "jangan dulu", "ga jadi", "batalin", "batalkan",
}


# ---------------------------------------------------------------------------
# Helper CHAT (AD-ENG-004): proyeksi aman utk context port & state ringkas.
# ---------------------------------------------------------------------------
def _msg_to_turn(msg: Message):
    """Konversi Message -> MessageTurn ringkas (non-secret) utk context port."""
    from sam.application.ux.conversational_reasoner import MessageTurn

    role = "assistant" if msg.role == MessageRole.ASSISTANT else "user"
    return MessageTurn(role=role, content=msg.content)


def _state_to_brief(state: Optional[UxMissionState]):
    """Proyeksi state mission aktif -> MissionBrief ringkas (tersanitasi) bila
    relevan; None bila tidak ada mission aktif (D-12 / Refinement Van).
    HANYA field ringkas tanpa secret."""
    from sam.application.ux.conversational_reasoner import MissionBrief

    if state is None:
        return None
    operation = (state.operation or "").strip()
    if not operation:
        return None  # tidak ada misi aktif yang relevan -> jangan sertakan
    return MissionBrief(
        operation=operation,
        status=(state.status or "").strip(),
        target=(state.target or "").strip(),
        summary=(state.what_sam_understood or "").strip(),
    )


def _relevant_evidence(state: Optional[UxMissionState]):
    """Evidence canonical yg relevan (bila sudah ada di state mission)."""
    from sam.governed_reasoning.structured_reasoning import EvidenceRef

    if state is None:
        return ()
    refs = []
    for e in state.evidence or []:
        if not isinstance(e, dict):
            continue
        refs.append(
            EvidenceRef(
                evidence_id=str(e.get("evidence_id") or e.get("url") or ""),
                source_type=str(e.get("source_type") or ""),
                source_id=str(e.get("url") or e.get("target") or ""),
            )
        )
    return tuple(refs)


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
        steps = "; ".join(f"{i + 1}. {s}" for i, s in enumerate(planned))
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
            e.get("url") or e.get("target") or e.get("detail") or str(e) for e in evidence
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
        conversational_reasoner: Optional["object"] = None,
        multi_mission: Optional["object"] = None,
        tenant: str = "default",
    ) -> None:
        """Wire repository conversation + MissionUXService (+ CHAT port).

        - conversation_repo: implementasi `ConversationRepository` (wajib;
          bisa InMemory utk dev/test, Postgres utk produksi). Bila None, dibuat
          InMemory (aman utk tes; produksi via endpoint meneruskan unit yg benar).
        - mission_service: instance `MissionUXService` (orchestrator misi canonical).
          Bila None, dibuat default `MissionUXService()` (tanpa persistence
          khusus -> perilaku in-memory default, aman & non-destruktif).
        - participant: identitas sisi user untuk conversation (default "user").
        - conversational_reasoner: implementasi application port
          `ConversationalReasoner` (READ-ONLY) utk jalur CHAT. Bila None, dibuat
          default `ProviderConversationalReasonerAdapter()` (adapter infra yang
          membungkus existing ProviderExecutor; infra di-inject DI, application
          tidak pernah memilih provider). (AD-ENG-004.)
        - multi_mission: instance `MultiMissionService` (AD-ENG-005 §7 coordination/
          registration boundary). Bila disediakan, jalur MISSION memanggil
          `MultiMissionService.submit_mission(tenant, ...)` yang memanggil
          `MissionUXService.submit()` lalu meregistrasikan canonical mission-*
          ke registry — sehingga Mission konversasi masuk Mission List (layer 2)
          tanpa membuat Mission kedua / m_*. Bila None, jalur MISSION memakai
          `mission_service.submit(...)` (perilaku lama, regresi S2-3 aman).
        - tenant: tenant aktif utk mission-command (default "default"), isolasi
          M12-012.
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
        self._multi_mission = multi_mission
        self._tenant = (tenant or "default").strip() or "default"
        self._participant = participant
        if conversational_reasoner is None:
            # Lazy import infra adapter (membungkus ProviderExecutor) — sama pola
            # lazy import ProviderExecutor di service._interpret_via_ai.
            from sam.application.ux.conversational_reasoner_adapter import (
                ProviderConversationalReasonerAdapter,
            )

            # Default Van (2026-08-16): Ollama lokal `gemma3:1b` sbg provider
            # utama CHAT (tanpa API key). Bila Ollama tak tersedia, fallback ke
            # DeepSeek bila env DEEPSEEK_API_KEY ada. (Sebelumnya default
            # deepseek-first; kini ollama-first sesuai keputusan Van.)
            conversational_reasoner = ProviderConversationalReasonerAdapter(
                provider_id="ollama",
                model_id="gemma3:1b",
                fallback_provider_id="deepseek",
                fallback_model_id="deepseek-chat",
            )
        self._reasoner = conversational_reasoner
        # W3: proposal percakapan yang menunggu konfirmasi CHAT (KONTEKS
        # percakapan, bukan state mission / state machine baru).
        self._pending: Optional[CCPending] = None

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
            if convo.participant == participant and convo.status == ConversationStatus.OPEN:
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
        ward_tenant: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Terima command user; orkestrasi ke MissionUXService; proyeksi assistant.

        Flow (orde ketat, kegagalan persist TIDAK diklaim sukses):
          1. persist user Message (gagal -> raise, 0 klaim sukses).
          2. (W3) bila ada proposal konfirmasi tertunda -> tangani jawaban CHAT
             (konfirmasi/tolak/pilih) — SEBELUM guard CHAT.
          3. (W3) bila permintaan read-only menarget Ward -> ajukan proposal +
             minta konfirmasi CHAT (belum eksekusi).
          4. lainnya -> panggil `MissionUXService.submit(text)` -> state.
          5. bangun assistant Message HANYA dari field state nyata.
          6. persist assistant Message (gagal -> penanda jujur).

        `ward_tenant` = username nyata pemohon (bila ada sesi login) utk resolusi/
        owner Ward (cross-tenant fail-closed). Default None -> "user".

        Returns dict:
            {
              "state": UxMissionState (canonical, dari MissionUXService),
              "conversation_id": str,
              "user_message_id": str,
              "assistant_message_id": str,
              "assistant_persisted": bool,
              "w3_pending": bool (opsional, penanda proposal konfirmasi),
            }
        """
        # Simpan tenant utk W3 (konfirmasi/proposal) & eksekusi policy-authorized.
        pending_tenant = (ward_tenant or "").strip() or "user"
        # 1) Persist user message TERLEBIH DAHULU (harus tersimpan sebelum apa pun).
        user_msg = self.append_user_message(conversation_id=conversation_id, content=text)

        # 1a) W3 — JAWABAN KONFIRMASI PERCAKAPAN (bukan approval formal).
        #     Jika ada proposal tertunda (`_pending`), pesan ini diproses sbg
        #     jawaban CHAT atas proposal itu (SEBELUM guard CHAT, karena "ya"/
        #     "tidak" juga cocok `_is_conversational`). Ini BUKAN state machine
        #     mission baru — hanya konteks percakapan di orchestrator conversation.
        #     Mutation TIDAK lewat sini untuk eksekusi: setelah konfirmasi, mutasi
        #     tetap masuk formal approval (`submit` -> WAITING_APPROVAL -> decide).
        from sam.application.ux.service import MissionUXService

        if self._pending is not None:
            return self._handle_confirmation_reply(
                conversation_id=conversation_id,
                text=text,
                user_msg=user_msg,
            )

        # 1b) DETEKSI CHAT (AD-ENG-004): percakapan biasa -> jalur CHAT via port
        #     `ConversationalReasoner` (READ-ONLY). TIDAK membuat MissionRequest /
        #     MissionPlan / Approval (acceptance Van: NO). Guard deterministik
        #     `_is_conversational` SAMA dengan `MissionUXService._interpret`
        #     (boundary 2026-08-16) -> CHAT vs MISSION konsisten & non-flaky.
        if MissionUXService._is_conversational(text):
            return self._submit_chat(
                conversation_id=conversation_id,
                text=text,
                user_msg=user_msg,
            )

        # 1c) W3 — PROPOSAL + KONFIRMASI CHAT utk observasi WARD eksternal
        #     (read-only). Dari sudut user, membaca/pentarikan Ward (mis.
        #     "Periksa OpenClaw saya") adalah permintaan yang walau read-only
        #     TETAP menuntut konfirmasi percakapan sebelum SAM benar-benar
        #     mengobservasi target di luar domain (W3: confirmation via CHAT,
        #     bukan approval). Bila permintaan menarget WARD yang cocok utk
        #     user → ajukan proposal & minta konfirmasi CHAT, TANPA `submit()`
        #     (belum ada mission → belum eksekusi). Read-only CITIZEN
        #     (local-machine) TIDAK tersentuh (W2 tetap policy-authorized).
        proposal = self._maybe_propose_ward_confirmation(
            conversation_id, text, user_msg, ward_tenant=pending_tenant
        )
        if proposal is not None:
            return proposal

        # 2) Orkestrasi ke MissionUXService -> state canonical.
        #    (Keputusan audit S2-3: TIDAK ada assosiasi `_mission_link` RAM.
        #    State mission canonical MILIK MissionUXService & survive restart via
        #    `_recover_from_store`; conversation tidak menyimpan duplikat sumber
        #    kebenaran mission agar tidak jadi "persistence kedua" diam-diam.)
        #    AD-ENG-005 §7 (Opsi 2): bila `multi_mission` disediakan, jalur
        #    MISSION lewat `MultiMissionService.submit_mission` -> memanggil
        #    MissionUXService.submit() + registrasikan canonical mission-* ke
        #    MissionRegistry (masuk Mission List) tanpa membuat Mission kedua.
        if self._multi_mission is not None:
            state = self._multi_mission.submit_mission(
                self._tenant,
                text,
                idempotency_key=idempotency_key,
            )
        else:
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
    # W3 — proposal + konfirmasi CHAT utk observasi Ward eksternal (read-only).
    # ------------------------------------------------------------------
    def _ward_manager_for(self, tenant: Optional[str] = None):
        """WardManager terikat tenant nyata pemohon (W3/W1).

        Reuse `_build_ward_manager_for_tenant` (service) sbg composition root
        Ward; ikat tenant utk owner-check (cross-tenant fail-closed). Bila Ward
        subsystem tak tersedia -> None.
        """
        from sam.application.ux.service import _build_ward_manager_for_tenant

        return _build_ward_manager_for_tenant(
            (tenant or "").strip() or "user"
        )

    @staticmethod
    def _is_citizen_ward_target(target: str) -> bool:
        """Apakah target adalah citizen environment (bukan Ward eksternal)?

        Sinkron dgn `_CITIZEN_ENV_TARGETS` di WardManager (Van #6): Walau target
        non-citizen yang tak terdaftar sbg Ward tetap lewat jalur existing,
        W3 HANYA mengintervensi saat target jelas menunjuk WARD milik user.
        """
        t = (target or "").strip().lower()
        return t in ("local-machine", "local", "localhost", "127.0.0.1")

    def _user_wards(self, manager, tenant: str):
        """Daftar Ward milik `tenant` (entrustment owner == tenant).

        Cross-tenant -> tidak disertakan (fail-closed). Mengembalikan list
        (ward_id, name).
        """
        if manager is None:
            return []
        out = []
        try:
            for w in manager.repository.list():
                ent = manager.repository.get_entrustment(w.identity.ward_id)
                owner = ((ent.owner_id if ent else "") or "").strip()
                if owner.split(":")[-1] == (tenant or "").strip():
                    out.append((w.identity.ward_id, w.name))
        except Exception:  # noqa: BLE001 - defensif
            return []
        return out

    @staticmethod
    def _ward_matches(target: str, name: str) -> bool:
        """Cocokkan target user dgn nama Ward (case-insensitive).

        Exact ATAU salah-satu memuat yang lain ("openclaw" vs "openclaw-prod").
        """
        t = (target or "").strip().lower().replace("saya", "").strip()
        n = (name or "").strip().lower()
        if not t or not n:
            return False
        return t == n or t in n or n in t

    def _maybe_propose_ward_confirmation(
        self,
        conversation_id: str,
        text: str,
        user_msg: Message,
        ward_tenant: Optional[str] = None,
    ) -> Optional[Dict[str, Any]]:
        """W3 — proposal + konfirmasi CHAT utk observasi WARD eksternal (read-only).

        HANYA intervensi bila permintaan read-only `environment.*` menarget
        WARD yang jelas milik user. Read-only CITIZEN (local-machine) TIDAK
        tersentuh (W2 tetap policy-authorized). Mutation juga tidak (formal
        approval existing).

        Return None bila bukan kasus W3 (jalur existing dipakai). Return Dict
        (shape submit_command) bila proposal konfirmasi diajukan. TIDAK
        memanggil `_mission.submit()` -> belum ada mission -> belum eksekusi.
        """
        from sam.application.ux.service import MissionUXService

        try:
            operation, target, understood, _planned, _act, _appr, _rr = (
                MissionUXService._interpret(text)
            )
        except Exception:  # noqa: BLE001 - gagal interpret -> jalur existing
            return None
        op = (operation or "").strip()
        # HANYA read-only environment.* yang relevan utk Ward (observe).
        if not op.startswith("environment."):
            return None
        if not MissionUXService._operation_is_read_only(op):
            return None
        target = (target or "").strip()
        if not target or self._is_citizen_ward_target(target):
            return None  # citizen / kosong -> jalur existing (W2)

        tenant = (ward_tenant or "").strip() or "user"
        mgr = self._ward_manager_for(tenant)
        user_wards = self._user_wards(mgr, tenant)
        matches = [
            (wid, name) for (wid, name) in user_wards
            if self._ward_matches(target, name)
        ]
        # Tak ada Ward milik user yang cocok -> jalur existing (akan resolve/
        # refused/bahkan citizen path), W3 tidak intervensi.
        if not matches:
            return None

        if len(matches) == 1:
            # CLEAR target (test A) -> proposal tunggal + minta konfirmasi CHAT.
            wid, name = matches[0]
            self._pending = CCPending(
                text=text,
                operation=operation,
                target=name,
                understood=understood,
                ward_tenant=tenant,
            )
            content = (
                f"SAM menemukan Ward '{name}' milik Anda. {understood}\n"
                "SAM AKAN mengobservasi Ward ini (read-only). Pastikan dulu: "
                f"lanjutkan mengobservasi '{name}'? (ya/tidak)"
            )
            return self._w3_reply(conversation_id=conversation_id, text=text,
                                  user_msg=user_msg, content=content,
                                  pending=True, reason=understood,
                                  proposal_kind="read_only", ward=name)

        # AMBIGUOUS target (test B) -> SAM bertanya via CHAT TANPA eksekusi.
        self._pending = CCPending(
            text=text,
            operation=operation,
            target="",
            understood=understood,
            ward_tenant=tenant,
            candidates=tuple(matches),
        )
        lines = [
            f"Ada {len(matches)} Ward yang cocok dengan permintaan Anda ({text.strip()}).",
            "Ward mana yang ingin Anda periksa? Pilih nomor atau nama:",
        ]
        for i, (wid, name) in enumerate(matches, 1):
            lines.append(f"  {i}. {name}")
        content = "\n".join(lines)
        # Ambiguous: state.jujur merepresentasikan PERTANYAAN pilihan (bukan
        # pemahaman generik) di what_sam_understood -> SAM benar-benar bertanya.
        return self._w3_reply(conversation_id=conversation_id, text=text,
                              user_msg=user_msg, content=content,
                              pending=True, reason=content,
                              proposal_kind="ambiguous", candidates=tuple(matches))

    def _handle_confirmation_reply(
        self,
        conversation_id: str,
        text: str,
        user_msg: Message,
    ) -> Dict[str, Any]:
        """W3 — tangani JAWABAN user atas proposal konfirmasi tertunda.

        DIPANGGIL HANYA saat `_pending` ADA (dicek di submit_command). Bukan
        approval formal: read-only tetap policy-authorized (W2) setelah konfirmasi.
        Mutation TIDAK dieksekusi di sini — setelah user konfirmasi, mission
        masuk formal approval (`submit` -> WAITING_APPROVAL -> decide).

        Alur:
          - ambiguous (ada candidates): user pilih nomor/nama -> set target ->
            interpret ulang -> minta konfirmasi lagi (test B).
          - proposal tunggal: "ya" -> submit + execute (read-only) ATAU submit
            saja (mutation, tunggu approval); "tidak" -> batal, tanpa eksekusi.
        """
        pending = self._pending
        low = (text or "").strip().lower()

        # --- AMBIGUOUS: user memilih nomor / nama ---
        if pending and pending.candidates:
            chosen = self._resolve_candidate_choice(low, pending.candidates)
            if chosen is None:
                # Pilihan tak dikenal -> tanya ulang (tetap pending, TANPA eksekusi).
                lines = [
                    f"Pilihan '{text.strip()}' tidak dikenal. Pilih nomor atau nama yang tersedia:",
                ]
                for i, (_wid, name) in enumerate(pending.candidates, 1):
                    lines.append(f"  {i}. {name}")
                return self._w3_reply(conversation_id, text, user_msg,
                                      content="\n".join(lines), pending=True,
                                      reason=pending.understood,
                                      proposal_kind="ambiguous",
                                      candidates=pending.candidates)
            _wid, _name = chosen
            # Set target ke kandidat terpilih -> proposal tunggal utk ward tsb.
            self._pending = CCPending(
                text=pending.text,
                operation=pending.operation,
                target=_name,
                understood=f"SAM akan mengobservasi Ward '{_name}'.",
                ward_tenant=pending.ward_tenant,
            )
            content = (
                f"SAM memilih Ward '{_name}'. SAM akan mengobservasi Ward ini "
                f"(read-only) . Lanjutkan mengobservasi '{_name}'? (ya/tidak)"
            )
            return self._w3_reply(conversation_id, text, user_msg,
                                  content=content, pending=True,
                                  reason=pending.understood,
                                  proposal_kind="read_only", ward=_name)

        # --- PROPOSAL TUNGGAL: konfirmasi / tolak ---
        if self._is_reject(text):
            # User menolak (test D) -> batal, TANPA eksekusi.
            self._pending = None
            content = (
                f"Baik, dibatalkan. SAM tidak mengobservasi Ward '{pending.target}' "
                "dan tidak melakukan apa pun (0 eksekusi)."
            )
            return self._w3_reply(conversation_id, text, user_msg,
                                  content=content, pending=False,
                                  reason="dibatalkan oleh user")
        if self._is_confirm(text):
            # Konfirmasi -> submit mission (canonical) + execute bila read-only.
            try:
                state = self._mission.submit(
                    pending.text, idempotency_key=None
                )
                _state = state
                # Read-only -> eksekusi canonical (W2 policy-authorized), dgn
                # tenant Ward nyata (cross-tenant fail-closed).
                if state.status == UxStateStatus.UNDERSTOOD and \
                        not state.approval_required:
                    _state = self._mission.execute_policy_authorized(
                        approver="policy:read_only",
                        ward_tenant=pending.ward_tenant,
                    )
                # Mutation -> setelah konfirmasi tetap formal approval
                # (WAITING_APPROVAL -> decide), TIDAK dieksekusi di sini.
            except Exception as exc:  # noqa: BLE001 - jujur, tanpa crash
                self._pending = None
                return self._w3_reply(
                    conversation_id, text, user_msg,
                    content=f"SAM gagal mengajukan misi: {exc}",
                    pending=False, reason="gagal",
                )
            self._pending = None
            assistant_content = _state_to_assistant_text(_state)
            return self._w3_reply(
                conversation_id, text, user_msg,
                content=assistant_content,
                pending=False,
                state=_state,
                reason=("eksekusi selesai" if _state.status in (
                    UxStateStatus.COMPLETED, UxStateStatus.BLOCKED,
                    UxStateStatus.FAILED, UxStateStatus.RETRYABLE)
                    else "menunggu approval formal"),
            )

        # Jawaban tak dikenal terhadap proposal tunggal -> tanya ulang.
        return self._w3_reply(
            conversation_id, text, user_msg,
            content=(
                f"SAM tidak memahami '{text.strip()}'. Lanjutkan mengobservasi "
                f"Ward '{pending.target}'? (ya/tidak)"
            ),
            pending=True, reason=pending.understood,
            proposal_kind="read_only", ward=pending.target,
        )

    @staticmethod
    def _is_confirm(text: str) -> bool:
        low = (text or "").strip().lower().strip(".!?")
        return low in _CONFIRM_WORDS

    @staticmethod
    def _is_reject(text: str) -> bool:
        low = (text or "").strip().lower().strip(".!?")
        return low in _REJECT_WORDS

    @staticmethod
    def _resolve_candidate_choice(low: str, candidates: tuple):
        """Resolve pilihan user (nomor / nama) ke salah satu kandidat. None bila."""
        low = (low or "").strip().lower().strip(".!?")
        # pilihan berupa nomor (1..N)
        if low.isdigit():
            idx = int(low) - 1
            if 0 <= idx < len(candidates):
                return candidates[idx]
            return None
        # pilihan berupa nama
        for wid, name in candidates:
            if name.lower() == low or low in name.lower():
                return (wid, name)
        return None

    def _w3_reply(
        self,
        conversation_id,
        text,
        user_msg,
        content: str,
        pending: bool,
        reason: str = "",
        state=None,
        proposal_kind: str = "",
        ward: str = "",
        candidates: tuple = (),
    ) -> Dict[str, Any]:
        """Bangun & persist assistant message utk jalur W3 (CHAT konfirmasi).

        `state` bila diberikan -> mission nyata (hasil eksekusi/await) utk ViewModel.
        Bila None -> proyeksi CHAT ringkas (bukan mission), status UNDERSTOOD.

        `proposal_kind` ("read_only" | "ambiguous" | "") + `ward` + `candidates`
        diteruskan sbg `w3_proposal` metadata agar UI tahu kapan menampilkan
        [Lanjutkan]/[Batalkan] (read-only) ATAU daftar pilihan (ambiguous).
        Contract existing CHAT: UI mengirim jawaban (ya/tidak/nomor/nama) ke
        `/ux/conversation/message` yang SAMA — BUKAN endpoint/approval baru.
        """
        if conversation_id is None:
            conversation_id = ""
        session = self._ensure_open_session(conversation_id)
        assistant_msg = Message(
            message_id=f"msg-{uuid.uuid4().hex[:12]}",
            role=MessageRole.ASSISTANT,
            content=content,
            conversation_id=conversation_id,
            session_id=session.session_id,
            evidence_refs=(),
            created_at=_now_utc(),
        )
        assistant_persisted = True
        try:
            if conversation_id:
                self._repo.append_message(assistant_msg)
        except Exception:  # noqa: BLE001 - penanda jujur
            assistant_persisted = False

        # Metadata proposal utk UI (tanpa secret). Hanya ada saat pending.
        w3_proposal = None
        if pending:
            w3_proposal = {
                "kind": proposal_kind or "read_only",
                "ward": ward,
                # candidates: list NAMA Ward (bukan tuple internal/id) utk UI.
                "candidates": [
                    (c[1] if isinstance(c, (tuple, list)) and len(c) > 1 else c)
                    for c in candidates
                ],
            }

        if state is not None:
            _state = state
        else:
            from sam.application.ux.state import UxMissionState

            _state = UxMissionState(
                request_id="",
                request_text=text,
                what_sam_understood=reason or content,
                operation="",
                target="",
                planned_steps=[],
                approval_required=False,
                action_summary="",
                approval_status=UxStateStatus.NONE,
                status=UxStateStatus.UNDERSTOOD,
            )
        return {
            "state": _state,
            "conversation_id": conversation_id,
            "user_message_id": user_msg.message_id,
            "assistant_message_id": assistant_msg.message_id,
            "assistant_persisted": assistant_persisted,
            "w3_pending": pending,
            "w3_proposal": w3_proposal,
        }

    # ------------------------------------------------------------------
    # 3b) jalur CHAT (AD-ENG-004): port ConversationalReasoner (READ-ONLY)
    # ------------------------------------------------------------------
    def _submit_chat(
        self,
        conversation_id: str,
        text: str,
        user_msg: Message,
    ) -> Dict[str, Any]:
        """Jalur CHAT: hasilkan respons percakapan via port `ConversationalReasoner`.

        AD-ENG-004 (Accepted):
          - TIDAK memanggil `MissionUXService.submit()` -> TIDAK ada pembuatan
            MissionRequest / MissionPlan / Approval (acceptance Van: NO).
          - Port READ-ONLY (`converse`) -> content jadi assistant message -> persist.
          - Idempotency & persistence tetap di `ConversationService.submit_command`.
          - Mission execution/governance pipeline TIDAK tersentuh.

        Returns dict (sama shape dengan submit_command):
          {
            "state": UxMissionState (CHAT projection ringkas, bukan MissionRequest),
            "chat": True,  # penanda jalur CHAT (utk acceptance/audit)
            "conversation_id": str,
            "user_message_id": str,
            "assistant_message_id": str,
            "assistant_persisted": bool,
          }
        """
        # Susun ConversationContext (sanitize; history terbatas = application
        # policy; active_mission & evidence HANYA bila relevan).
        history_msgs = list(self._repo.list_messages(conversation_id))
        # Hanya pesan non-secret; opsi history ≤ 8 turn terbaru (application policy).
        turns = [
            _msg_to_turn(m)
            for m in history_msgs
            if m.message_id != user_msg.message_id  # user message dipakai sbg `user_message`
        ][-8:]

        from sam.application.ux.conversational_reasoner import (
            ConversationContext,
        )

        mission_brief = _state_to_brief(self._mission.get_state())
        ctx = ConversationContext(
            conversation_id=conversation_id,
            user_message=text,
            history=tuple(turns),
            evidence_refs=_relevant_evidence(self._mission.get_state()),
            active_mission=mission_brief,
            language_hint="id",
        )
        response = self._reasoner.converse(ctx)

        session = self._ensure_open_session(conversation_id)
        assistant_msg = Message(
            message_id=f"msg-{uuid.uuid4().hex[:12]}",
            role=MessageRole.ASSISTANT,
            content=response.content,
            conversation_id=conversation_id,
            session_id=session.session_id,
            evidence_refs=(),
            created_at=_now_utc(),
        )

        # Persist assistant message. Bila gagal -> penanda jujur, bukan klaim sukses.
        assistant_persisted = True
        try:
            self._repo.append_message(assistant_msg)
        except Exception:  # noqa: BLE001 — defnsif; jangan mengklaim sukses
            assistant_persisted = False

        # State CHAT projection ringkas (BUKAN MissionRequest/Plan/Approval).
        chat_state = UxMissionState(
            request_id="",
            request_text=text,
            what_sam_understood=("SAM memahami: ini percakapan biasa (CHAT), bukan perintah misi."),
            operation="",
            target="",
            planned_steps=[],
            approval_required=False,
            action_summary="",
            approval_status=UxStateStatus.NONE,
            status=UxStateStatus.UNDERSTOOD,
        )
        chat_state.observability = {
            "request_id": "",
            "mission_id": "",
            "status": UxStateStatus.UNDERSTOOD,
            "capability": "chat",
            "external_target": "",
            "start_time": _now_utc(),
            "end_time": "",
            "verification_result": "",
            "failure_reason": "",
            "approver": "",
        }

        return {
            "state": chat_state,
            "chat": True,
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
