"""
Metrics Routes — SAM Runtime API
"""

from fastapi import APIRouter
from ...telemetry.service import TelemetryService

router = APIRouter()


@router.get("/")
async def get_metrics():
    """Ambil metrics runtime terkini."""
    telemetry = TelemetryService()
    m = telemetry.get_metrics()

    if m is None:
        return {
            "status": "no_data",
            "message": "No metrics collected yet.",
        }

    return {
        "status": "ok",
        "timestamp": m.timestamp.isoformat(),
        "cpu_percent": m.cpu_percent,
        "memory_mb": round(m.memory_mb, 1),
        "uptime_seconds": round(m.uptime_seconds, 1),
        "workflow_count": m.workflow_count,
        "plugin_count": m.plugin_count,
        "health_score": m.health_score,
    }
