"""Health Routes - SAM REST API (Program J, J2 rewire).

Menggantikan `WebRuntimeService()` instansiasi langsung dengan jalur resmi
`runtime_service.api` (ConversationPreviewGateway.api.health()) via DI.
TIDAK mengubah RuntimeService. health berasal dari RuntimeAPI.health().
"""
from __future__ import annotations

from fastapi import APIRouter, HTTPException


def _gateway():
    """Gateway jalur resmi (dibangun di wiring). Import lazy agar tidak circular."""
    from ..wiring import conversation_preview_gateway
    return conversation_preview_gateway


router = APIRouter()


@router.get("/")
async def health():
    """Root health check via jalur resmi RuntimeAPI.health()."""
    health_view = _gateway().api.health()
    data = getattr(health_view, "as_dict", lambda: {})()
    state = str(data.get("status", "degraded"))
    healthy = state in ("healthy", "ready", "ok")

    return {
        "status": "healthy" if healthy else "degraded",
        "state": state,
        "service": "SAM Runtime",
    }


@router.get("/ready")
async def ready():
    """Readiness probe - OK hanya jika runtime siap menerima kerja."""
    health_view = _gateway().api.health()
    data = getattr(health_view, "as_dict", lambda: {})()
    state = str(data.get("status", "degraded"))
    ready_state = state in ("healthy", "ready", "ok")

    if not ready_state:
        raise HTTPException(
            status_code=503,
            detail={"state": state, "message": "Runtime not ready"},
        )

    return {
        "status": "ready",
        "state": state,
    }
