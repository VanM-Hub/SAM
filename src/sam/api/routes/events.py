"""
Events Routes — SAM Runtime API
"""

from typing import Optional
from fastapi import APIRouter, Query
from ...telemetry.service import TelemetryService
from ...telemetry.models import TelemetrySeverity

router = APIRouter()


@router.get("/")
async def get_events(
    limit: int = Query(100, ge=1, le=1000, description="Maksimal event"),
    severity: Optional[str] = Query(None, description="Filter severity"),
):
    """Ambil event telemetry.

    Args:
        limit: Maksimal event yang dikembalikan (max 1000).
        severity: Filter berdasarkan severity (trace/debug/info/warning/error/critical).
    """
    telemetry = TelemetryService()

    sev = None
    if severity:
        try:
            sev = TelemetrySeverity(severity.lower())
        except ValueError:
            sev = None

    events = telemetry.get_events(limit=limit, severity=sev)

    return {
        "total": len(events),
        "events": [
            {
                "event_id": e.id,
                "event_name": e.message,
                "timestamp": e.timestamp.isoformat(),
                "severity": e.severity.value,
                "component": e.component.value,
                "category": e.category.value,
                "correlation_id": e.correlation_id,
                "session_id": e.session_id,
                "payload": e.metadata,
            }
            for e in events
        ],
    }
