"""Runtime Routes - SAM REST API (Program J, J2 rewire).

Menggantikan import langsung `RuntimeCoordinator` dengan jalur resmi
`runtime_service.api` (ConversationPreviewGateway.api.status()) via DI.
TIDAK ada akses langsung ke Runtime citizens. TIDAK mengubah RuntimeService.
"""
from __future__ import annotations

from fastapi import APIRouter


def _gateway():
    """Gateway jalur resmi (dibangun di wiring). Import lazy agar tidak circular."""
    from ..wiring import conversation_preview_gateway
    return conversation_preview_gateway


router = APIRouter()


@router.get("/")
async def runtime_status():
    """Status runtime via jalur resmi RuntimeAPI.status()."""
    status_view = _gateway().api.status()
    data = getattr(status_view, "as_dict", lambda: {})()

    return {
        "services": data.get("services", {}),
        "version": data.get("version", "27.0.0"),
        "healthy": data.get("healthy", True),
    }
