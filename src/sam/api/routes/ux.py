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

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel

from sam.application.ux.approval import ApprovalDecisionIntent
from sam.application.ux.service import MissionUXService


class SubmitRequest(BaseModel):
    """Body request: apa yang manusia minta (bahasa alami, bukan struktur internal)."""
    text: str


class DecideRequest(BaseModel):
    """Body request: keputusan approval user."""
    intent: str  # "approve" | "reject"
    approver: str = "user"


class UxRoutes:
    """Factory adapter — memegang satu instance MissionUXService (composition)."""

    def __init__(self) -> None:
        self.service = MissionUXService()


_routes = UxRoutes()
router = APIRouter(tags=["ux"])


@router.post("/submit")
async def ux_submit(request: SubmitRequest):
    """Terima mission dari user, SAM pahami, susun rencana, taruh WAITING_APPROVAL.

    Adapter murni: meneruskan text ke MissionUXService.submit, mengembalikan
    UxMissionState.as_dict() (ViewModel) untuk UI. Tidak ada eksekusi di sini.
    """
    state = _routes.service.submit(request.text)
    return state.as_dict()


@router.get("/state")
async def ux_state():
    """Kembalikan ViewModel state saat ini (read-only)."""
    state = _routes.service.get_state()
    if state is None:
        return {"request_id": None, "message": "belum ada mission"}
    return state.as_dict()


@router.post("/decide")
async def ux_decide(request: DecideRequest):
    """Terapkan keputusan approval user (approve/reject).

    Adapter murni: meneruskan intent ke MissionUXService.decide, yang
    memanggil ApprovalGate canonical lalu (bila approved) menjalankan mission
    nyata via jalur canonical. UI tidak membuat jalur eksekusi sendiri.
    """
    try:
        intent = ApprovalDecisionIntent(request.intent)
    except ValueError:
        return {"error": "intent harus 'approve' atau 'reject'"}

    state = _routes.service.decide(intent, approver=request.approver)
    return state.as_dict()


@router.get("/evidence")
async def ux_evidence():
    """Evidence chain untuk operator (M9-004)."""
    return {"evidence": _routes.service.get_evidence()}


@router.get("/audit")
async def ux_audit():
    """Audit trail untuk operator."""
    return {"audit": _routes.service.get_audit()}
