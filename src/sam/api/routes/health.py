"""
Health Routes — SAM Runtime API
"""

from fastapi import APIRouter, HTTPException
from ...runtime_service import WebRuntimeService

router = APIRouter()


@router.get("/")
async def health():
    """Root health check — return OK jika runtime aktif.

    S10 (TDR): pindah dari direct-wiring RuntimeCoordinator ke WebRuntimeService
    (jalur resmi, AD-ENG-002). Sumber state = lifecycle service.
    """
    service = WebRuntimeService()
    service.initialize()
    status = service.status_dict()
    state = status["status"]
    healthy = state in ("ready", "running")

    return {
        "status": "healthy" if healthy else "degraded",
        "state": state,
        "service": "SAM Runtime",
    }


@router.get("/ready")
async def ready():
    """Readiness probe — return OK hanya jika runtime siap menerima kerja."""
    service = WebRuntimeService()
    service.initialize()
    status = service.status_dict()
    state = status["status"]
    ready_state = state in ("ready", "running")

    if not ready_state:
        raise HTTPException(
            status_code=503,
            detail={"state": state, "message": "Runtime not ready"},
        )

    return {
        "status": "ready",
        "state": state,
    }
