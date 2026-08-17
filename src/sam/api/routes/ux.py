"""UX Mission Routes - SAM REST API (M9-002).

Production UX Mission Entry Point: HTTP adapter untuk MissionUXService.

Clean Architecture (keputusan M9):
    HTML/UI -> REST Route (adapter) -> MissionUXService (Application Use Case)
             -> ApprovalGate canonical -> Mission canonical -> GitHub connector

Modul ini HANYA adapter. Ia memetakan HTTP request menjadi panggilan
Application Use Case (`MissionUXService` dari `sam.application.ux.service`).
Route TIDAK mengambil alih orchestration, TIDAK mengevaluasi policy/approval,
TIDAK menyentuh mission/execution/connector secara langsung, TIDAK memegang
kredensial. Seluruh otoritas tetap di boundary canonical.

UI (browser) HANYA fetch ke endpoint server ini — TIDAK pernah fetch langsung
ke GitHub atau adapter lain. Jalur wajib: UI -> MissionUXService -> canonical.
"""
from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Cookie, Header, HTTPException, Response
from pydantic import BaseModel

from sam.application.ux.approval import ApprovalDecisionIntent
from sam.application.ux.conversation import ConversationService
from sam.application.ux.identity import SessionStore, UserStore
from sam.application.ux.mission_registry import MultiMissionService
from sam.application.ux.service import MissionUXService
from sam.application.ux.persistence import build_conversation_persistence_unit

# Pengemasan pesan conversation untuk ViewModel/response (S2-3). Hanya field
# publik non-secret; credential/token TIDAK pernah dimasukkan.
def _message_to_viewmodel(msg) -> dict:
    return {
        "message_id": msg.message_id,
        "role": str(msg.role.value if hasattr(msg.role, "value") else msg.role),
        "content": msg.content,
        "conversation_id": msg.conversation_id,
        "session_id": msg.session_id,
        "evidence_refs": list(msg.evidence_refs or []),
        "created_at": msg.created_at,
    }


class SubmitRequest(BaseModel):
    """Body request: apa yang manusia minta (bahasa alami, bukan struktur internal)."""
    text: str
    # M10-005: Idempotency-Key optional — same key -> same logical operation.
    idempotency_key: Optional[str] = None


class DecideRequest(BaseModel):
    """Body request: keputusan approval user.

    AD-ENG-006 (Mission-Scoped Decision Targeting):
      `mission_id` WAJIB. Without it -> HTTP 422 (strict; zero mutation; tidak ada
      fallback ke current/latest/request_id/m_*). Body bentuk:
        {"intent": "approve"|"reject", "mission_id": "mission-<hex>"}

    M11-004: `approver` TIDAK lagi dipercaya dari client ketika AUTH aktif
    (SAM_ENABLE_AUTH=1). Identitas diambil dari sesi (header Authorization),
    bukan dari body ini. Field dipertahankan utk kompatibilitas mode non-auth.
    """
    intent: str  # "approve" | "reject"
    # AD-ENG-006: canonical mission-* target WAJIB. Field `Optional` (bukan
    # required) supaya auth/authorization (401/403) menang SEBELUM validasi
    # mission_id (422) — tidak bocorkan kebutuhan mission_id dgn info tak
    # terautentikasi. Validasi wajib dilakukan MANUAL di handler (setelah
    # `_require_auth`): missing -> HTTP 422 strict, zero mutation, tanpa
    # fallback ke current/latest/request_id/m_*.
    mission_id: Optional[str] = None
    approver: str = "user"


class ConversationMessageRequest(BaseModel):
    """Body request conversation (S2-3).

    conversation_id:
      - kosong/None -> ConversationService membuat/resume conversation default
        (ID stabil per participant, dibuat jika belum ada).
      - diisi & dikenal -> resume conversation tsb.
      - diisi & TIDAK dikenal -> fail-closed (HTTP 404), BUKAN dibuat diam-diam.
    text: apa yang user kirim (bahasa alami). Harus non-kosong.
    idempotency_key: optional (M10-005 retry-safe).
    """
    text: str
    conversation_id: Optional[str] = None
    idempotency_key: Optional[str] = None


class LoginRequest(BaseModel):
    username: str
    password: str


class RegisterRequest(BaseModel):
    """Buat akun baru (self-service dari UI). Password minimal 6 char."""

    username: str
    password: str
    role: str = "operator"


class UxRoutes:
    """Factory adapter — memegang satu instance MissionUXService (composition).

    M11-004: memegang UserStore + SessionStore utk production identity. AUTH
    diaktifkan via env `SAM_ENABLE_AUTH=1` (opt-in, default off) — sehingga
    jalur dev/test lama (approver string dari body) TIDAK berubah (regresi),
    dan production bisa mewajibkan login nyata.
    """

    def __init__(self) -> None:
        self.service = MissionUXService()
        # AD-ENG-005: unit persistence MISSION utk enumerasi Mission List
        # (repository durable = sumber enumerasi, §3.1). Dibangun DULU agar
        # factory mission-konversasi & MultiMissionService memakai unit yang SAMA.
        self.mission_unit = None
        self._mission_repo_blocked_reason = ""
        self._init_mission_persistence()
        # AD-ENG-005 §7 (Opsi 2): MultiMissionService = coordination/registration
        # boundary utk Mission dari Conversation. Factory memanggil MissionUXService
        # dengan persistence unit MISSION yang SAMA dgn unit enumerasi Mission List
        # (self.mission_unit), sehingga Mission konversasi persist ke repo yang
        # SAMA dengan yang dibaca /ux/missions (deterministik). MultiMissionService
        # TIDAK membuat Mission identity kedua; ia meregistrasikan canonical
        # mission-* hasil `submit()` ke registry.
        # AD-ENG-006 §5.3: `persistence_unit` di-inject utk durable fallback pada
        # decide (resolve live > durable; registry miss != mission missing).
        self.multi = MultiMissionService(
            service_factory=self._build_mission_service,
            persistence_unit=self.mission_unit,
        )
        self.users = UserStore()
        self.sessions = SessionStore()
        # S2-3: ConversationService (adapter HTTP conversation). Repository
        # conversation dipilih sesuai environment: InMemory utk dev/test,
        # PostgreSQL utk produksi (fail-closed saat PG tidak siap).
        self._conv_blocked_reason = ""
        from sam.application.ux.repositories import InMemoryConversationRepository

        _repo = InMemoryConversationRepository()
        try:
            _unit, _info = build_conversation_persistence_unit()
            if not (_info.get("production") and not _info.get("ready", True)):
                # produksi siap ATAU bukan produksi -> pakai backend yg dipilih
                _repo = _unit.conversations
            else:
                # produksi fail-closed: PG conversation tidak siap -> endpoint
                # menolak (503); TIDAK fallback menyimpan ke in-memory.
                self._conv_blocked_reason = _info.get("reason", "persistence unavailable")
        except Exception:  # pragma: no cover — defensif, jangan crash server
            _repo = InMemoryConversationRepository()
        self.conversations = ConversationService(
            conversation_repo=_repo,
            mission_service=self.service,
            multi_mission=self.multi,
        )

    def _init_mission_persistence(self) -> None:
        """Bangun unit persistence MISSION utk enumerasi Mission List (ADR-005 §3.1).

        Memakai `build_persistence_unit()` (factory yang sama dgn service) dgn
        logika ready: dev (bukan produksi) -> unit apa pun yg dipilih factory
        (InMemory) dipakai; produksi fail-closed (PG down) -> mission_unit=None
        & blocked_reason di-set (route /ux/missions menolak 503).
        """
        from sam.application.ux.persistence import build_persistence_unit

        try:
            _unit, _info = build_persistence_unit()
        except Exception as exc:  # pragma: no cover — defensif
            self._mission_repo_blocked_reason = f"mission persistence init gagal: {exc}"
            self.mission_unit = None
            return
        if _info.get("production") and not _info.get("ready", True):
            # produksi fail-closed: PG tidak siap -> jangan pakai InMemory fallback
            self.mission_unit = None
            self._mission_repo_blocked_reason = _info.get(
                "reason", "mission persistence unavailable"
            )
            return
        self.mission_unit = _unit

    @property
    def mission_repo(self) -> Optional[object]:
        """Repository mission durable utk enumerasi Mission List (ADR-005 §3.1).

        Baca dari `self.mission_unit.missions` (unit yang SAMA dipakai factory
        mission-konversasi utk persist). None bila persistence tidak tersedia
        (produksi fail-closed) — route /ux/missions -> 503.
        """
        if self.mission_unit is None:
            return None
        return getattr(self.mission_unit, "missions", None)

    def _build_mission_service(self):
        """Factory MissionUXService utk MultiMissionService (AD-ENG-005 §7).

        Inject persistence unit MISSION (`self.mission_unit`) sehingga Mission
        yang lahir dari Conversation dipersist ke repository yang SAMA dengan
        enumerasi Mission List (deterministik, sinkron di dev/prod).
        """
        return MissionUXService(persistence=self.mission_unit)

    @property
    def production(self) -> bool:
        """True saat SAM_ENV=production (M12-011: auth mandatory + secure cookie)."""
        return os.environ.get("SAM_ENV") == "production"

    @property
    def auth_enabled(self) -> bool:
        """AUTH aktif bila SAM_ENABLE_AUTH=1 ATAU produksi (M12-011 mandatory).

        Dinamis agar test bisa set per-case. Di produksi, login WAJIB (tidak
        ada jalur anonymous utk approve).
        """
        return os.environ.get("SAM_ENABLE_AUTH") == "1" or self.production

    @staticmethod
    def _extract_token(
        authorization: Optional[str], cookie: Optional[str] = None
    ) -> Optional[str]:
        """Ambil token dari header Bearer (prioritas) ATAU cookie httpOnly.

        M11-005: browser mengirim token via cookie httpOnly (tanpa localStorage),
        sehingga token tidak pernah tersentuh JS. Header Bearer tetap didukung
        utk kompatibilitas API/test langsung.
        """
        if authorization and authorization.lower().startswith("bearer "):
            return authorization[7:].strip()
        return (cookie or "").strip() or None

    def _require_auth(
        self,
        authorization: Optional[str],
        cookie: Optional[str] = None,
        csrf_header: Optional[str] = None,
    ) -> dict:
        """Wajibkan identitas terverifikasi (M11-004).

        Mengembalikan dict {'username','role'} bila token valid & role berwenang,
        else raise HTTPException 401/403. Dipanggil HANYA saat AUTH aktif.

        M12-011 (Identity Hardening):
          - cookie mode: bila identitas berasal dari cookie httpOnly, mutasi
            wajib sertakan X-CSRF-Token yang cocok dgn csrf sesi -> DENIED bila
            salah (cross-site request forge).
          - expired/revoked/forged token -> 401 (anonymous DENIED).
          - cross-user: identitas TIDAK pernah diambil dari body; selalu dari
            sesi terverifikasi.
        """
        # tanpanya (dev anonymous) -> default utk kompatibilitas regresi
        if not self.auth_enabled:
            return {"username": "user", "role": "operator"}
        token = self._extract_token(authorization, cookie)
        identity = self.sessions.authenticate(token)
        if not identity:
            raise HTTPException(
                status_code=401, detail="autentikasi diperlukan (login dulu)"
            )
        # CSRF wajib bila identitas datang via cookie (browser auto-attach
        # cookie utk request lintas-site); token bearer tidak ter-expose ke
        # cookie jadi tak butuh CSRF.
        if authorization is None and cookie:
            if not self.sessions.verify_csrf(token, csrf_header):
                raise HTTPException(status_code=403, detail="CSRF token tidak valid")
        if not self.users.can_operate(identity.get("role", "")):
            raise HTTPException(
                status_code=403,
                detail="role tidak berwenang melakukan keputusan approval",
            )
        return identity

    # ------------------------------------------------------------------
    # AD-ENG-005 — Mission List (Layer 2, read-only)
    # ------------------------------------------------------------------
    @staticmethod
    def _project_mission_card(mission_id: str, data: Optional[dict]) -> Optional[dict]:
        """Proyeksi `UxMissionState.as_dict()` -> card aman (non-secret).

        HANYA field ringkas (ADR §4.1). Tidak pernah menampilkan secrets /
        evidence mentah sensitif. Mengembalikan None bila data tidak ada/invalid.
        """
        if not isinstance(data, dict):
            return None
        understanding = data.get("understanding") or {}
        plan = data.get("plan") or {}
        execution = data.get("execution") or {}
        observability = data.get("observability") or {}
        # Lifecycle status canonical (UxStateStatus); fallback ke observability.
        status = (
            execution.get("status")
            or observability.get("status")
            or data.get("status")
            or "unknown"
        )
        return {
            "mission_id": mission_id,
            "status": status,
            "what_sam_understood": understanding.get("what_sam_understood") or "",
            "operation": understanding.get("operation") or "",
            "target": understanding.get("target") or "",
            "updated_at": data.get("updated_at") or "",
            "approval_required": bool(plan.get("approval_required", False)),
        }

    def _live_registry_state(
        self, tenant: str, mission_id: str
    ) -> Optional[dict]:
        """Ambil state live dari MissionRegistry utk mission-* (bila ada).

        ADR §3.2: live runtime state (registry ACTIVE entry) menang. Untuk
        Opsi-2 (1 command = 1 mission-*), tiap mission-* punya <= 1 entry di
        registry (execution_id = mission-*). Ambil entry pertama yang cocok.
        Bila tidak ada entry -> None (pakai durable).
        """
        reg = self.multi.registry()
        keys = reg.list_keys(tenant=tenant, mission_id=mission_id)
        if not keys:
            return None
        # Ambil entry live (terakhir ditulis = status paling segar).
        latest = keys[-1]
        return reg.get(tenant, latest["mission_id"], latest.get("execution_id"))

    def _list_mission_cards(self, tenant: str):
        """Enumerasi Mission List (ADR §3.1): repository durable + overlay registry.

        - Enumerasi dari repository durable (mission-*): deterministik, survive
          restart (registry kosong TIDAK menghilangkan mission).
        - Overlay live state dari MissionRegistry bila ada (precedence live > durable).
        - Bila persistence tidak tersedia (produksi fail-closed) -> HTTP 503.
        Proyeksi card non-secret; urut updated_at menurun.
        """
        repo = self.mission_repo
        if repo is None:
            raise HTTPException(
                status_code=503,
                detail=self._mission_repo_blocked_reason
                or "mission persistence tidak tersedia (fail-closed)",
            )
        mission_ids = repo.list_missions()
        cards = []
        for mid in mission_ids:
            live = self._live_registry_state(tenant, mid)
            if live is not None:
                card = self._project_mission_card(mid, live)
            else:
                durable = repo.load_mission(mid)
                card = self._project_mission_card(mid, durable)
            if card is not None:
                cards.append(card)
        cards.sort(key=lambda c: c.get("updated_at") or "", reverse=True)
        return cards

    def _get_mission_card(self, tenant: str, mission_id: str):
        """Detail satu mission (ADR §4.2): live registry state ATAU durable repo.

        Precedence §3.2: live > durable. TIDAK ada fallback mission-* ->
        request_id / m_*. Not found -> None (route -> 404).
        """
        live = self._live_registry_state(tenant, mission_id)
        if live is not None:
            return self._project_mission_card(mission_id, live)
        repo = self.mission_repo
        if repo is None:
            raise HTTPException(
                status_code=503,
                detail=self._mission_repo_blocked_reason
                or "mission persistence tidak tersedia (fail-closed)",
            )
        durable = repo.load_mission(mission_id)
        return self._project_mission_card(mission_id, durable)


# Cookie httpOnly pembawa token sesi (M11-005). Browser mengirimnya otomatis;
# token TIDAK pernah disimpan di JS (tanpa localStorage) — memenuhi hardening M9-008.
SESSION_COOKIE = "sam_session"

_routes = UxRoutes()
router = APIRouter(tags=["ux"])


@router.post("/submit")
async def ux_submit(request: SubmitRequest):
    """Terima mission dari user, SAM pahami, susun rencana, taruh WAITING_APPROVAL.

    Adapter murni: meneruskan text ke MissionUXService.submit, mengembalikan
    UxMissionState.as_dict() (ViewModel) untuk UI. Tidak ada eksekusi di sini.
    M10-005: `idempotency_key` memastikan retry TIDAK membuat mission ganda.

    AD-ENG-006: mission yang lahir di sini didaftarkan ke `multi` (live registry)
    agar dapat ditarget oleh `POST /ux/decide` (yang WAJIB mission_id & memakai
    MultiMissionService.decide sebagai boundary). TIDAK membuat Mission kedua/
    m_* baru — ia meregistrasikan mission-* yang SAMA dr state ini.
    """
    state = _routes.service.submit(request.text, idempotency_key=request.idempotency_key)
    # AD-ENG-006: daftarkan mission-* eksisting ke multi (tanpa identity kedua)
    # sehingga decide boundary `MultiMissionService.decide` bisa menargetkannya.
    mid = ((state.observability or {}).get("mission_id") or "").strip()
    if mid:
        _routes.multi.register("default", mid, _routes.service)
    return state.as_dict()


@router.get("/state")
async def ux_state():
    """Kembalikan ViewModel state saat ini (read-only)."""
    state = _routes.service.get_state()
    if state is None:
        return {"request_id": None, "message": "belum ada mission"}
    return state.as_dict()


@router.get("/missions")
async def ux_missions():
    """Mission List (Layer 2, read-only — AD-ENG-005 §3/§4.1).

    Enumerasi dari repository durable (mission-*) + overlay live state dari
    MissionRegistry (precedence live > durable). Read-only: TIDAK membuat /
    mengubah mission, TIDAK approve/execute/verify. Output: array card
    non-secret.
    """
    return {"missions": _routes._list_mission_cards("default")}


@router.get("/missions/{mission_id}")
async def ux_missions_detail(mission_id: str):
    """Detail satu mission (Layer 2, read-only — AD-ENG-005 §4.2).

    Lookup: live registry state ATAU durable repository state (precedence
    §3.2). TIDAK ada fallback mission-* -> request_id / m_*. Not found -> 404
    (fail-closed). Approval/execution tetap via canonical decide(), BUKAN di sini.
    """
    card = _routes._get_mission_card("default", mission_id)
    if card is None:
        raise HTTPException(status_code=404, detail="mission tidak ditemukan")
    return card


@router.post("/decide")
async def ux_decide(
    request: DecideRequest,
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
    x_csrf_token: Optional[str] = Header(None),
):
    """Terapkan keputusan approval user (approve/reject) utk mission target eksplisit.

    AD-ENG-006 (Mission-Scoped Decision Targeting, APPROVED/IMPLEMENTATION AUTHORIZED):
      - Resolve target Mission TERLEBIH DAHULU, baru decision terjadi. TIDAK ada
        urutan mutate-then-resolve.
      - Request BENTUK `{intent, mission_id}`. `mission_id` canonical mission-* WAJIB;
        tanpa mission_id -> HTTP 422 `mission_id_required` (zero mutation).
      - Route memakai `MultiMissionService.decide(...)` sebagai single application
        coordination boundary (bukan `_routes.service.decide` current).
      - Resolution (tenant, mission_id): live registry > durable repository;
        registry miss != mission missing. Unknown / cross-tenant -> generic 404
        `MISSION_NOT_FOUND` (anti existence oracle). Tidak ada fallback ke
        current/latest/request_id/m_*.
      - Governance didelegasikan `MultiMissionService` -> `MissionUXService.decide`
        -> ApprovalGate canonical -> existing execution (ADR-003 idempotency).
      - TIDAK ada endpoint baru, TIDAK ada identitas baru, tidak ada orchestration kedua.

    M11-004: bila AUTH aktif (SAM_ENABLE_AUTH=1), identitas diambil dari
    header Authorization (sesi login), BUKAN dari `approver` body. Tanpa token
    valid / role tidak berwenang -> 401/403 (tidak ada eksekusi).
    M12-011: saat identitas datang via cookie httpOnly, wajib X-CSRF-Token
    (proteksi CSRF) -> DENIED bila tidak cocok.
    """
    try:
        intent = ApprovalDecisionIntent(request.intent)
    except ValueError:
        return {"error": "intent harus 'approve' atau 'reject'"}

    # M11-004/M12-011: identitas terverifikasi dari sesi (bila auth aktif),
    # dengan proteksi CSRF utk jalur cookie. Dalam mode non-auth (default),
    # `approver` body tetap dipakai utk kompatibilitas regresi. Auth dicek
    # SEBELUM mission_id (401/403 tidak membocorkan keberadaan mission).
    identity = _routes._require_auth(authorization, sam_session, x_csrf_token)

    # AD-ENG-006: mission_id WAJIB -> 422 strict, zero mutation.
    if not (request.mission_id or "").strip():
        raise HTTPException(
            status_code=422,
            detail={
                "error": "mission_id wajib untuk decision request (target eksplisit)",
                "code": "mission_id_required",
            },
        )

    approver = (
        identity.get("username", "user")
        if _routes.auth_enabled
        else (request.approver or "user")
    )

    # AD-ENG-006: decision boundary = MultiMissionService.decide(tenant, mission_id,
    # execution_id, intent, approver). execution_id utk mission-* di-set = mission_id
    # (konsisten dgn submit_mission yang men-save registry dgn execution_id=mission-*;
    # AD-ENG-005 §8.1 execution_id confusion tetap follow-up, TIDAK disentuh di sini).
    # Resolve mission dgn tenant "default" (isolasi M12-012; reverse-proxy/identity
    # tenant scoping lanjutan di M11-004).
    try:
        state = _routes.multi.decide(
            tenant="default",
            mission_id=request.mission_id,
            execution_id=request.mission_id,
            intent=intent,
            approver=approver,
        )
    except KeyError:
        # unknown / cross-tenant -> generic 404 (anti existence oracle; zero mutation).
        raise HTTPException(
            status_code=404,
            detail={
                "error": "mission tidak ditemukan atau bukan milik tenant Anda",
                "code": "MISSION_NOT_FOUND",
            },
        )
    return state


@router.post("/conversation/message")
async def ux_conversation_message(request: ConversationMessageRequest):
    """Kirim pesan/command ke conversation (S2-3).

    Adapter murni -> ConversationService (orchestrator) -> MissionUXService
    -> canonical runtime. Response ViewModel berisi conversation + messages +
    mission state (semua non-secret).

    - conversation_id kosong -> create/resume conversation default (ID stabil).
    - conversation_id diisi & tidak dikenal -> 404 fail-closed (BUKAN dibuat
      diam-diam; acceptance "conversation ID tidak dikenal").
    - text kosong -> 422 validation error (BUKAN mission execution).
    - produksi fail-closed conversation -> 503 (PG tidak siap).
    """
    if _routes._conv_blocked_reason:
        raise HTTPException(
            status_code=503,
            detail=f"conversation persistence tidak tersedia: {_routes._conv_blocked_reason}",
        )
    text = (request.text or "").strip()
    if not text:
        raise HTTPException(
            status_code=422, detail="field `text` tidak boleh kosong"
        )

    # Resolve conversation: resume yang diminta (fail-closed bila tidak dikenal)
    # ATAU create/resume default bila tidak disebutkan.
    if request.conversation_id:
        if not _routes.conversations.conversation_exists(request.conversation_id):
            # fail-closed: conversation tidak dikenal -> 404, tidak membuat.
            raise HTTPException(
                status_code=404,
                detail="conversation tidak dikenal — kirim tanpa conversation_id utk membuat yang baru",
            )
        cid = request.conversation_id
    else:
        convo = _routes.conversations.create_or_resume_conversation()
        cid = convo.conversation_id

    result = _routes.conversations.submit_command(
        conversation_id=cid, text=text, idempotency_key=request.idempotency_key
    )
    state = result["state"]
    messages = _routes.conversations.get_conversation(cid)
    header = _routes.conversations.get_conversation_header(cid)
    return {
        "conversation_id": cid,
        "conversation": {
            "conversation_id": cid,
            "title": (header.title if header else ""),
            "status": (
                str(header.status.value if hasattr(header.status, "value") else header.status)
                if header else ""
            ),
        },
        "messages": [_message_to_viewmodel(m) for m in messages],
        "assistant_persisted": result["assistant_persisted"],
        "mission_state": (state.as_dict() if state is not None else None),
    }


@router.get("/conversation/{conversation_id}")
async def ux_conversation_get(conversation_id: str):
    """Baca conversation + messages + mission state (S2-3, read-only)."""
    if _routes._conv_blocked_reason:
        raise HTTPException(
            status_code=503,
            detail=f"conversation persistence tidak tersedia: {_routes._conv_blocked_reason}",
        )
    if not _routes.conversations.conversation_exists(conversation_id):
        raise HTTPException(
            status_code=404, detail="conversation tidak dikenal"
        )
    messages = _routes.conversations.get_conversation(conversation_id)
    header = _routes.conversations.get_conversation_header(conversation_id)
    state = _routes.conversations.get_mission_state()
    return {
        "conversation_id": conversation_id,
        "conversation": {
            "conversation_id": conversation_id,
            "title": (header.title if header else ""),
            "participant": (header.participant if header else ""),
            "status": (
                str(header.status.value if hasattr(header.status, "value") else header.status)
                if header else ""
            ),
        },
        "messages": [_message_to_viewmodel(m) for m in messages],
        "mission_state": (state.as_dict() if state is not None else None),
    }


@router.post("/login")
async def ux_login(request: LoginRequest, response: Response):
    """Login -> set cookie httpOnly + kembalikan identitas user (M11-004/M11-005).

    Verifikasi credential terhadap UserStore (users.json di luar project).
    Berhasil -> buat sesi, set cookie httpOnly `sam_session`, kembali
    {token, user:{username, role}}. Password TIDAK pernah dikembalikan/dilog.
    `token` di body tetap dikembalikan utk kompatibilitas API/test langsung.
    """
    identity = _routes.users.verify(request.username, request.password)
    if not identity:
        raise HTTPException(status_code=401, detail="username atau password salah")
    token = _routes.sessions.login(identity)
    # M12-011: `secure` hanya saat produksi (HTTPS). Dev (http) tak set secure
    # agar cookie tetap bisa dipakai di lokal http. HttpOnly+SameSite tetap.
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=_routes.production,
        path="/",
    )
    # kembalikan csrf token sekali (produksi/cookie mode perlu utk mutasi)
    return {"token": token, "user": identity, "csrf": _routes.sessions.csrf_for(token)}


@router.post("/register")
async def ux_register(request: RegisterRequest, response: Response):
    """Buat akun baru dari UI (self-service register).

    - Menulis user ke UserStore (users.json di luar project, hash pbkdf2).
    - Username sudah ada -> 409 Conflict (bukan 500).
    - Password terlalu pendek -> 422 (pydantic min_length bila dipakai) / 400.
    - Setelah dibuat, langsung buat sesi + set cookie httpOnly (auto-login).
    - Password TIDAK pernah dikembalikan/dilog.
    """
    username = (request.username or "").strip()
    password = request.password or ""
    if not username:
        raise HTTPException(status_code=400, detail="username wajib diisi")
    if len(password) < 6:
        raise HTTPException(status_code=400, detail="password minimal 6 karakter")
    try:
        identity = _routes.users.create_user(username, password, role=request.role)
    except ValueError as exc:
        # duplikat username
        raise HTTPException(status_code=409, detail=str(exc)) from exc

    token = _routes.sessions.login(identity)
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        secure=_routes.production,
        path="/",
    )
    return {
        "created": True,
        "user": identity,
        "token": token,
        "csrf": _routes.sessions.csrf_for(token),
    }


@router.post("/logout")
async def ux_logout(
    response: Response,
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
):
    """Logout - revoke sesi token + cookie httpOnly (M11-004/M11-005/M12-011)."""
    token = _routes._extract_token(authorization, sam_session)
    # M12-011: revoke (tandai tak valid) + hapus sesi (defense in depth)
    _routes.sessions.revoke(token)
    _routes.sessions.logout(token)
    response.delete_cookie(key=SESSION_COOKIE, path="/")
    return {"ok": True, "message": "logged out"}


@router.get("/me")
async def ux_me(
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
):
    """Identitas user yang sedang login (M11-004). Bila auth nonaktif, kembali
    identitas default 'user' utk kebutuhan UI."""
    if not _routes.auth_enabled:
        return {"authenticated": False, "user": {"username": "user", "role": "operator"}}
    token = _routes._extract_token(authorization, sam_session)
    identity = _routes.sessions.authenticate(token)
    if not identity:
        raise HTTPException(status_code=401, detail="belum login")
    return {
        "authenticated": True,
        "user": identity,
        # CSRF utk sesi aktif (double-submit): UI butuh ini pd page-load
        # (cookie httpOnly sudah ada) supaya mutasi pertama tak 403.
        "csrf": _routes.sessions.csrf_for(token),
    }


@router.get("/evidence")
async def ux_evidence():
    """Evidence chain untuk operator (M9-004)."""
    return {"evidence": _routes.service.get_evidence()}


@router.get("/audit")
async def ux_audit():
    """Audit trail untuk operator."""
    return {"audit": _routes.service.get_audit()}
