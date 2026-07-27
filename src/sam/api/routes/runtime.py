"""
Runtime Routes — SAM Runtime API
"""

from fastapi import APIRouter
from ...runtime.coordinator import RuntimeCoordinator

router = APIRouter()


@router.get("/")
async def runtime_status():
    """Status runtime saat ini."""
    coord = RuntimeCoordinator()

    # Dapatkan nama adapter dengan aman
    adapter_name = "Unknown"
    if hasattr(coord, "adapter_name") and coord.adapter_name:
        adapter_name = coord.adapter_name
    elif hasattr(coord, "hosting_adapter") and coord.hosting_adapter:
        adapter_name = coord.hosting_adapter.__class__.__name__.replace("Adapter", "")

    # Dapatkan uptime
    uptime = 0
    if hasattr(coord, "start_time") and coord.start_time:
        from datetime import datetime
        uptime = (datetime.utcnow() - coord.start_time).total_seconds()

    return {
        "state": coord.state.value,
        "hosting": adapter_name,
        "uptime_seconds": uptime,
        "session": coord.session_manager.get_current_session()["id"]
        if hasattr(coord, "session_manager")
        else "none",
        "plugins": {
            "loaded": 14,
            "expected": 14,
        },
    }
