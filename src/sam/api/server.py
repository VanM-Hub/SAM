"""SAM REST API - Host (Program J).

FastAPI server dengan endpoints REST (JSON):
  - /health           health check (jalur resmi runtime_service.api)
  - /health/ready     readiness probe
  - /runtime          status runtime (jalur resmi)
  - /events           event telemetry
  - /metrics          metrics terkini
  - /workflow         workflow capability (jalur resmi)
  - /policy           policy capability
  - /audit            audit capability
  - /preview          preview capability (preview only)
  - /knowledge        knowledge capability
  - /memory           memory capability
  - /artifact         artifact capability
  - /approval         approval (pass-through)
  - /status           status runtime
  - /                 metadata API

Seluruh endpoint yang berhubungan dengan capability memakai `runtime_service.api`
via wiring (composition root di `wiring.py`). TIDAK ada import langsung ke
Runtime/Registry/Provider/Connector/ExecutionRuntime di route handler.

Run:
    uvicorn sam.api.server:app --host 0.0.0.0 --port 8080
"""
from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse

from .routes import health, runtime, events, metrics, mission
from .routes import ux as ux_routes
from .routes import citizens
from .routes import wards
from .wiring import rest_app

app = FastAPI(
    title="SAM Runtime API",
    description="SAM - AI Operations Guardian Runtime API",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers (jalur resmi capability ada di rest_app.routers)
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(runtime.router, prefix="/runtime", tags=["runtime"])
app.include_router(events.router, prefix="/events", tags=["events"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])
app.include_router(mission.router, prefix="/mission", tags=["mission"])
app.include_router(ux_routes.router, prefix="/ux", tags=["ux"])
app.include_router(citizens.router, prefix="/citizens", tags=["citizens"])
app.include_router(wards.router, prefix="/wards", tags=["wards"])

# Program J: capability REST (workflow/policy/audit/preview/knowledge/memory/
# artifact/approval/status) - composition-only, via runtime_service.api.
for _router in rest_app.routers:
    app.include_router(_router.router)


@app.on_event("startup")
async def _ward_bootstrap_on_startup():
    """Pastikan OpenClaw Ward terdaftar + persisted (Postgres) saat boot.

    `bootstrap_openclaw_ward` (via `get_ward_manager`) bersifat lazy di
    composition root - baru jalan saat endpoint /wards atau percakapan Ward
    pertama diakses. Hook ini memicu lebih awal supaya Ward terdaftar dan
    tersimpan ke PostgreSQL segera setelah server hidup (Ward tahan restart).
    Aman idempotent: bootstrap TIDAK menimpa entri/konsen yang sudah ada.
    """
    try:
        from sam.ward.wiring import get_ward_manager
        get_ward_manager()
    except Exception:  # noqa: BLE001 - startup tak boleh gagal karena Ward
        pass


@app.get("/ui", response_class=HTMLResponse)
async def mission_workspace_ui():
    """SAM Mission Workspace --- thin client UI ke SAM production capability.
    File baseline = v18 (Phase 1 wired ke /ux/*). UI lama dihapus."""
    ui_file = Path(__file__).resolve().parent / "static" / "mission_workspace.html"
    return FileResponse(ui_file, media_type="text/html")


@app.get("/")
async def root():
    return {
        "message": "SAM Runtime API",
        "version": "1.0",
        "endpoints": {
            "health": "/health",
            "ready": "/health/ready",
            "runtime": "/runtime",
            "metrics": "/metrics",
            "events": "/events",
            "workflow": "/workflow",
            "policy": "/policy",
            "audit": "/audit",
            "preview": "/preview/{execution_id}",
            "knowledge": "/knowledge",
            "memory": "/memory",
            "artifact": "/artifact",
            "approval": "/approval/{execution_id}",
            "status": "/status",
            "mission": "/mission/{mission_id}",
            "citizens": "/citizens",
        },
    }
