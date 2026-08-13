"""
Metrics Routes — SAM Runtime API (M12-008 Observability).

GET /metrics -> telemetri nyata dalam format Prometheus text (bounded,
tanpa label unbounded). Sumber: registry `sam.application.ux.metrics` yang
disuntik dari service/persistence (mission_received, mission_blocked,
execution_started/completed/failed, idempotency_replay/conflict,
persistence_error).
"""
from fastapi import APIRouter, Response

from sam.application.ux.metrics import metrics as _metrics

router = APIRouter()


@router.get("/")
async def get_metrics():
    """Ekspos telemetri SAM dalam format Prometheus text (M12-008)."""
    body = _metrics.render_prometheus()
    return Response(
        content=body,
        media_type="text/plain; version=0.0.4",
    )
