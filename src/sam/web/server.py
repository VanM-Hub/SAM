"""
SAM Web Dashboard — Phase 1

FastAPI + Jinja2 + HTMX dashboard untuk SAM Operations Console.
Ringan, cepat, tanpa build frontend.
"""

import asyncio
from pathlib import Path
from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from ..runtime.coordinator import RuntimeCoordinator
from ..runtime_service import WebRuntimeService
from ..telemetry.service import TelemetryService
from ..intelligence.detector import IncidentDetector
from ..autonomous.executor import ActionExecutor
from ..autonomous.models import AutonomousActionStatus
from ..openclaw.discovery import OpenClawDiscovery
from ..openclaw.health import OpenClawHealthCollector

WEB_DIR = Path(__file__).parent

app = FastAPI(title="SAM Operations Console", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static & templates
app.mount("/static", StaticFiles(directory=str(WEB_DIR / "static")), name="static")
templates = Jinja2Templates(directory=str(WEB_DIR / "templates"))

# Services (singleton)
# WebRuntimeService = consumer produksi pertama RuntimeService (Session 01).
# Gateway kontrak & lifecycle untuk Web Runtime/Lifecycle/Status endpoint.
# BUKAN executor/coordinator; data runtime nyata tetap dari coordinator.
runtime_service = WebRuntimeService()
runtime_service.initialize()  # lifecycle -> ready
coordinator = RuntimeCoordinator()
telemetry = TelemetryService()
incident_detector = IncidentDetector(coordinator.workspace_path)
action_executor = ActionExecutor(coordinator)
openclaw_discovery = OpenClawDiscovery()
openclaw_health = OpenClawHealthCollector()


@app.get("/")
async def index(request: Request):
    """Dashboard utama."""
    state = coordinator.state.value
    healthy = state in ("ready", "running", "healthy")
    health_str = "HEALTHY" if healthy else "DEGRADED"
    # WebRuntimeService: status lifecycle service (consumer RuntimeService).
    service_status = runtime_service.status_dict()
    metrics = telemetry.get_metrics()

    loop = asyncio.get_event_loop()
    incidents = await incident_detector.detect()
    pending = action_executor.get_pending_actions()
    workspaces = await openclaw_discovery.discover()

    return templates.TemplateResponse("index.html", {
        "request": request,
        "state": state.upper(),
        "health": health_str,
        "healthy": healthy,
        "runtime_service": service_status,
        "metrics": metrics,
        "incidents": incidents[:6],
        "incident_count": len(incidents),
        "pending_actions": pending[:5],
        "pending_count": len(pending),
        "openclaw_found": len(workspaces) > 0,
        "openclaw_count": len(workspaces),
        "platform": "Web Dashboard",
    })


@app.get("/runtime")
async def runtime_page(request: Request):
    """Runtime detail."""
    state = coordinator.state.value
    metrics = telemetry.get_metrics()
    adapter_name = coordinator.adapter_name
    # WebRuntimeService: lifecycle & contract untuk Runtime endpoint.
    service_status = runtime_service.status_dict()

    return templates.TemplateResponse("runtime.html", {
        "request": request,
        "state": state.upper(),
        "hosting": adapter_name,
        "runtime_service": service_status,
        "metrics": metrics,
        "workspace": coordinator.workspace_path,
        "autonomous": coordinator.autonomous_enabled,
    })


@app.get("/workflow")
async def workflow_page(request: Request):
    """Workflow monitor."""
    workflows = [
        {"id": "wf-001", "name": "Health Check Cycle", "status": "running", "progress": 60},
        {"id": "wf-002", "name": "Provider Connectivity Test", "status": "pending", "progress": 0},
        {"id": "wf-003", "name": "Knowledge Import", "status": "completed", "progress": 100},
        {"id": "wf-004", "name": "Plugin Discovery", "status": "running", "progress": 35},
    ]
    return templates.TemplateResponse("workflow.html", {
        "request": request,
        "workflows": workflows,
    })


@app.get("/incidents")
async def incidents_page(request: Request):
    """Incident dashboard."""
    incidents = await incident_detector.detect()
    return templates.TemplateResponse("incidents.html", {
        "request": request,
        "incidents": incidents,
        "total": len(incidents),
        "critical": len([i for i in incidents if i.severity.value == "critical"]),
        "high": len([i for i in incidents if i.severity.value == "high"]),
        "medium": len([i for i in incidents if i.severity.value == "medium"]),
        "low": len([i for i in incidents if i.severity.value == "low"]),
    })


@app.get("/autonomous")
async def autonomous_page(request: Request):
    """Autonomous actions."""
    pending = action_executor.get_pending_actions()
    history = action_executor.get_history(limit=20)
    completed = action_executor.get_actions_by_status(AutonomousActionStatus.COMPLETED)
    failed = action_executor.get_actions_by_status(AutonomousActionStatus.FAILED)
    denied = action_executor.get_actions_by_status(AutonomousActionStatus.DENIED)

    return templates.TemplateResponse("autonomous.html", {
        "request": request,
        "pending": pending,
        "history": history,
        "completed_count": len(completed),
        "failed_count": len(failed),
        "denied_count": len(denied),
        "pending_count": len(pending),
    })


@app.get("/openclaw")
async def openclaw_page(request: Request):
    """OpenClaw integration."""
    workspaces = await openclaw_discovery.discover()
    health = None
    if workspaces:
        health = await openclaw_health.collect(workspaces[0].path)

    return templates.TemplateResponse("openclaw.html", {
        "request": request,
        "workspaces": workspaces,
        "health": health,
    })


@app.get("/knowledge")
async def knowledge_page(request: Request, q: str = ""):
    """Knowledge explorer."""
    from ..intelligence.knowledge import KnowledgeLookup

    lookup = KnowledgeLookup()
    if q:
        items = await lookup.search(q)
    else:
        items = await lookup.search("")

    return templates.TemplateResponse("knowledge.html", {
        "request": request,
        "knowledge": items,
        "query": q,
    })


@app.get("/settings")
async def settings_page(request: Request):
    """Settings (read-only)."""
    from pathlib import Path as PPath
    ws = PPath(coordinator.workspace_path)

    dos_path = ws / "desired-state.yaml"
    mission_path = ws / "mission.yaml"

    dos_content = ""
    mission_content = ""

    if dos_path.exists():
        try:
            dos_content = dos_path.read_text(encoding="utf-8")
        except Exception:
            dos_content = "Error reading DOS"

    if mission_path.exists():
        try:
            mission_content = mission_path.read_text(encoding="utf-8")
        except Exception:
            mission_content = "Error reading Mission"

    return templates.TemplateResponse("settings.html", {
        "request": request,
        "dos": dos_content,
        "mission": mission_content,
    })


def run_server(host: str = "127.0.0.1", port: int = 8080):
    """Jalankan server web dashboard."""
    print("SAM Operations Console starting on http://{0}:{1}".format(host, port))
    uvicorn.run(app, host=host, port=port)
