"""
Health Routes — SAM Runtime API
"""

from fastapi import APIRouter, HTTPException
from ...runtime.coordinator import RuntimeCoordinator

router = APIRouter()


@router.get("/")
async def health():
    """Root health check — return OK jika runtime aktif."""
    coord = RuntimeCoordinator()
    state = coord.state.value
    healthy = state in ("ready", "running", "healthy")

    return {
        "status": "healthy" if healthy else "degraded",
        "state": state,
        "service": "SAM Runtime",
    }


@router.get("/ready")
async def ready():
    """Readiness probe — return OK hanya jika runtime siap menerima kerja."""
    coord = RuntimeCoordinator()
    state = coord.state.value
    ready_state = state in ("ready", "running", "healthy")

    if not ready_state:
        raise HTTPException(
            status_code=503,
            detail={"state": state, "message": "Runtime not ready"},
        )

    return {
        "status": "ready",
        "state": state,
    }
