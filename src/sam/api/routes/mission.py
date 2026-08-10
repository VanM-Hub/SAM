"""Mission Routes - SAM REST API (Program P2A).

Production Mission Entry Point: HTTP adapter untuk MissionBuilder.

Clean Architecture (keputusan P2A):
    HTTP -> REST Route (adapter) -> Application Use Case -> AgentBridge/AgentRuntime -> MissionBuilder

Modul ini HANYA adapter: memetakan HTTP request menjadi panggilan Application Use Case
(`AgentBridge.run_mission_from_provider` dari `api.llm_wiring`). AgentBridge adalah
application-level use case yang memegang wiring:
    build_plan -> MissionBuilder.build_default() -> PlanResult -> AgentRuntime.run_mission().

Route TIDAK mengambil alih orchestration. TIDAK mengubah RuntimeService, Governance,
Execution, maupun reasoning/engine.py. External_calls tetap 0 (preview-only, deterministik).
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter
from pydantic import BaseModel


class MissionRequest(BaseModel):
    """Body request untuk menjalankan mission (application-level DTO)."""
    provider_id: str = "openai"
    mission_id: str = "mission-default"


def _bridge():
    """Application Use Case (AgentBridge) - lazy import agar tidak circular.

    Composition root di `api.llm_wiring` membangun `llm_agent_bridge` (AgentBridge)
    yang memegang AgentRuntime + MissionBuilder (Mission Builder).
    """
    from ..llm_wiring import llm_agent_bridge
    return llm_agent_bridge


def _result_details(result) -> dict:
    """Petakan AgentRunResult -> dict (serializer adapter, composition-only).

    AgentRunResult mengekspos `steps` (jumlah langkah yang dijalankan) + `detail`,
    bukan objek plan (plan hanya hidup selama eksekusi internal AgentRuntime).
    """
    return {
        "mission_id": getattr(result, "mission_id", ""),
        "ok": bool(getattr(result, "ok", False)),
        "final_state": getattr(result, "final_state", ""),
        "external_calls": int(getattr(result, "external_calls", 0)),
        "steps": int(getattr(result, "steps", 0)),
        "detail": str(getattr(result, "detail", "")),
    }


router = APIRouter(tags=["mission"])


@router.post("/{mission_id}")
async def run_mission(mission_id: str, request: Optional[MissionRequest] = None):
    """Jalankan mission via Application Use Case (AgentBridge -> MissionBuilder).

    - Pilih mission_id dari path; jika body ada, provider_id diambil dari body.
    - Ini production mission entry point pertama (P2A).
    """
    provider_id = request.provider_id if request else "openai"
    result = _bridge().run_mission_from_provider(provider_id, mission_id)
    return _result_details(result)


@router.get("/")
async def list_agents():
    """Daftar agent mission yang teraktivasi (read-only, via composition root)."""
    registry = _bridge()._layer.registry
    return {"agents": registry.list_ids()}
