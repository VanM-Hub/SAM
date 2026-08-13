"""Health Routes - SAM REST API (Program J, J2 rewire).

Menggantikan `WebRuntimeService()` instansiasi langsung dengan jalur resmi
`runtime_service.api` (ConversationPreviewGateway.api.health()) via DI.
TIDAK mengubah RuntimeService. health berasal dari RuntimeAPI.health().
"""
from __future__ import annotations

import os

from fastapi import APIRouter, HTTPException


def _gateway():
    """Gateway jalur resmi (dibangun di wiring). Import lazy agar tidak circular."""
    from ..wiring import conversation_preview_gateway
    return conversation_preview_gateway


def _persistence_prod_ready() -> bool:
    """M12-007 Readiness: cek persistence produksi (fail-closed).

    Saat SAM_ENV=production (atau PG dikonfigurasi), readiness HANYA true bila
    PostgreSQL tersedia & reachable. Non-produksi -> True (dev tidak fail-closed)."""
    env = os.environ.get("SAM_ENV", "").strip()
    dsn = os.environ.get("SAM_PG_DSN", "").strip()
    # Hanya wajib saat produksi: SAM_ENV=production, atau PG dikonfigurasi eksplisit.
    if env != "production" and not (dsn or os.environ.get("SAM_ENABLE_PG") == "1"):
        return True
    try:
        from sam.application.ux import persistence as _pers
        _unit, info = _pers.build_persistence_unit()
        return bool(info.get("ready"))
    except Exception:
        # Gagal menilai -> anggap not-ready (fail-safe) untuk produksi.
        return False


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
    """Readiness probe - OK hanya jika runtime siap menerima kerja.

    M12-007: saat produksi (SAM_ENV=production / PG dikonfigurasi), readiness
    juga mewajibkan persistence PostgreSQL siap (fail-closed). PG down -> 503
    NOT READY, konsisten dengan M12-004/005 (tanpa fallback diam-diam)."""
    health_view = _gateway().api.health()
    data = getattr(health_view, "as_dict", lambda: {})()
    state = str(data.get("status", "degraded"))
    ready_state = state in ("healthy", "ready", "ok")

    pers_ok = _persistence_prod_ready()
    if not ready_state or not pers_ok:
        raise HTTPException(
            status_code=503,
            detail={
                "state": state,
                "readiness": "ready" if ready_state else "runtime-degraded",
                "persistence": "ready" if pers_ok else "production-persistence-unavailable",
                "message": "Not ready",
            },
        )

    return {
        "status": "ready",
        "state": state,
        "persistence": "ready",
    }
