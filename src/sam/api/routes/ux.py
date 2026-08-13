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
from sam.application.ux.identity import SessionStore, UserStore
from sam.application.ux.service import MissionUXService


class SubmitRequest(BaseModel):
    """Body request: apa yang manusia minta (bahasa alami, bukan struktur internal)."""
    text: str
    # M10-005: Idempotency-Key optional — same key -> same logical operation.
    idempotency_key: Optional[str] = None


class DecideRequest(BaseModel):
    """Body request: keputusan approval user.

    M11-004: `approver` TIDAK lagi dipercaya dari client ketika AUTH aktif
    (SAM_ENABLE_AUTH=1). Identitas diambil dari sesi (header Authorization),
    bukan dari body ini. Field dipertahankan utk kompatibilitas mode non-auth.
    """
    intent: str  # "approve" | "reject"
    approver: str = "user"


class LoginRequest(BaseModel):
    username: str
    password: str


class UxRoutes:
    """Factory adapter — memegang satu instance MissionUXService (composition).

    M11-004: memegang UserStore + SessionStore utk production identity. AUTH
    diaktifkan via env `SAM_ENABLE_AUTH=1` (opt-in, default off) — sehingga
    jalur dev/test lama (approver string dari body) TIDAK berubah (regresi),
    dan production bisa mewajibkan login nyata.
    """

    def __init__(self) -> None:
        self.service = MissionUXService()
        self.users = UserStore()
        self.sessions = SessionStore()

    @property
    def auth_enabled(self) -> bool:
        """AUTH aktif bila env SAM_ENABLE_AUTH=1. Dinamis agar test bisa set per-case."""
        return os.environ.get("SAM_ENABLE_AUTH") == "1"

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
        self, authorization: Optional[str], cookie: Optional[str] = None
    ) -> dict:
        """Wajibkan identitas terverifikasi (M11-004).

        Mengembalikan dict {'username','role'} bila token valid & role berwenang,
        else raise HTTPException 401/403. Dipanggil HANYA saat AUTH aktif.
        """
        if not self.auth_enabled:
            return {"username": "user", "role": "operator"}
        token = self._extract_token(authorization, cookie)
        identity = self.sessions.authenticate(token)
        if not identity:
            raise HTTPException(
                status_code=401, detail="autentikasi diperlukan (login dulu)"
            )
        if not self.users.can_operate(identity.get("role", "")):
            raise HTTPException(
                status_code=403,
                detail="role tidak berwenang melakukan keputusan approval",
            )
        return identity


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
    """
    state = _routes.service.submit(request.text, idempotency_key=request.idempotency_key)
    return state.as_dict()


@router.get("/state")
async def ux_state():
    """Kembalikan ViewModel state saat ini (read-only)."""
    state = _routes.service.get_state()
    if state is None:
        return {"request_id": None, "message": "belum ada mission"}
    return state.as_dict()


@router.post("/decide")
async def ux_decide(
    request: DecideRequest,
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
):
    """Terapkan keputusan approval user (approve/reject).

    Adapter murni: meneruskan intent ke MissionUXService.decide, yang
    memanggil ApprovalGate canonical lalu (bila approved) menjalankan mission
    nyata via jalur canonical. UI tidak membuat jalur eksekusi sendiri.

    M11-004: bila AUTH aktif (SAM_ENABLE_AUTH=1), identitas diambil dari
    header Authorization (sesi login), BUKAN dari `approver` body. Tanpa token
    valid / role tidak berwenang -> 401/403 (tidak ada eksekusi).
    """
    try:
        intent = ApprovalDecisionIntent(request.intent)
    except ValueError:
        return {"error": "intent harus 'approve' atau 'reject'"}

    # M11-004: identitas terverifikasi dari sesi (bila auth aktif). Dalam mode
    # non-auth (default), `approver` body tetap dipakai utk kompatibilitas regresi.
    identity = _routes._require_auth(authorization, sam_session)
    approver = (
        identity.get("username", "user")
        if _routes.auth_enabled
        else (request.approver or "user")
    )

    state = _routes.service.decide(intent, approver=approver)
    return state.as_dict()


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
    response.set_cookie(
        key=SESSION_COOKIE,
        value=token,
        httponly=True,
        samesite="lax",
        path="/",
    )
    return {"token": token, "user": identity}


@router.post("/logout")
async def ux_logout(
    response: Response,
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
):
    """Logout — hapus sesi token + cookie httpOnly (M11-004/M11-005)."""
    token = _routes._extract_token(authorization, sam_session)
    if _routes.sessions.logout(token):
        response.delete_cookie(key=SESSION_COOKIE, path="/")
        return {"ok": True, "message": "logged out"}
    return {"ok": False, "message": "sudah tidak ada sesi / token tidak valid"}


@router.get("/me")
async def ux_me(
    authorization: Optional[str] = Header(None),
    sam_session: Optional[str] = Cookie(None),
):
    """Identitas user yang sedang login (M11-004). Bila auth nonaktif, kembali
    identitas default 'user' utk kebutuhan UI."""
    if not _routes.auth_enabled:
        return {"authenticated": False, "user": {"username": "user", "role": "operator"}}
    identity = _routes.sessions.authenticate(
        _routes._extract_token(authorization, sam_session)
    )
    if not identity:
        raise HTTPException(status_code=401, detail="belum login")
    return {"authenticated": True, "user": identity}


@router.get("/evidence")
async def ux_evidence():
    """Evidence chain untuk operator (M9-004)."""
    return {"evidence": _routes.service.get_evidence()}


@router.get("/audit")
async def ux_audit():
    """Audit trail untuk operator."""
    return {"audit": _routes.service.get_audit()}
