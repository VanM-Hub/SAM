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
from ..presentation import PresentationLayer
from ..runtime_service.api import (
    RuntimeAPI,
    PreviewRequestView,
    wire_execution_preview,
    ConversationPreviewGateway,
)
from ..execution_runtime.execution_engine import ExecutionEngine
from ..execution_runtime.execution_request import ExecutionRequest
from ..execution_runtime.execution_runtime import ExecutionRuntime
from ..execution_runtime.execution_pipeline import ExecutionPipeline
from ..execution_runtime.provider_activation import ProviderActivationExecutor
from ..providers.execution.provider_executor import ProviderExecutor as RealProviderExecutor
from ..runtime_service.api import KnowledgePreviewConsumer
from ..knowledge_runtime.foundation.knowledge_registry import KnowledgeRegistry
from ..workflow_runtime.foundation.workflow_registry import WorkflowRegistry
from ..runtime_service.api import WorkflowPreviewConsumer
from ..artifact_runtime.foundation.artifact_registry import ArtifactRegistry
from ..runtime_service.api import ArtifactPreviewConsumer
from ..memory.foundation.memory_registry import MemoryRegistry
from ..runtime_service.api import MemoryPreviewConsumer
from ..policy_runtime.foundation.policy_registry import PolicyRegistry
from ..runtime_service.api import PolicyPreviewConsumer
from ..audit_runtime.foundation.audit_registry import AuditRegistry
from ..runtime_service.api import AuditPreviewConsumer
from ..telemetry.service import TelemetryService
from ..telemetry.collector import MetricsCollector
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
# --- Session 04 (AD-S04): Presentation Layer menerima RuntimeService via DI ---
# Desktop = Presentation pertama. Presentation HANYA membaca kontrak RuntimeService
# (lifecycle/status/descriptor/metadata/contract), tidak tahu coordinator/execution.
presentation_layer = PresentationLayer(runtime_service=runtime_service)
# --- Session 10 fix: web metrics (bug pre-existing) ---
# Template index/runtime memakai metrics.cpu_percent/memory_mb/uptime_seconds/
# workflow_count/plugin_count/health_score. TelemetryService TIDAK punya get_metrics;
# MetricsCollector.metrics menyediakan cpu/uptime; field lain diberi nilai aman.
_metrics_collector = MetricsCollector()


def _web_metrics() -> dict:
    """Bangun dict metrics yg kompatibel dgn template web (bugfix pre-existing)."""
    m = _metrics_collector.metrics
    return {
        "cpu_percent": round(m.cpu_percent, 1),
        "memory_mb": round(m.memory_percent, 0),
        "uptime_seconds": round(m.uptime_seconds, 0),
        "workflow_count": 0,
        "plugin_count": 0,
        "health_score": 100.0 if m.last_error is None else 0.0,
    }


coordinator = RuntimeCoordinator()
telemetry = TelemetryService()
incident_detector = IncidentDetector(coordinator.workspace_path)
action_executor = ActionExecutor(coordinator)
openclaw_discovery = OpenClawDiscovery()
openclaw_health = OpenClawHealthCollector()

# --- Session 01: RuntimeAPI -> ExecutionRuntime (producer preview pertama) ---
# Routing/composition dilakukan di entry (web), bukan di dalam RuntimeService,
# agar RuntimeService tetap gateway (tidak mengetahui provider/execution).
# Producer menghasilkan ExecutionRequest(mode="preview") dan memanggil
# ExecutionEngine.execute(). Provider TIDAK dieksekusi (preview, ADR-024).
runtime_api = RuntimeAPI()
# --- Session 03: Provider Resolution (AD-S03-001) ---
# Hubungkan jalur resmi preview ke provider layer VIA mekanisme resmi
# (ProviderActivationExecutor -> RealProviderExecutor). Provider dapat
# di-resolve/di-select (identity & metadata tersedia), TETAPI execute()
# TIDAK dipanggil: mode preview => external_calls=0, executed=false.
# Tidak ada executor/provider/pipeline baru; hanya dependency injection.
_provider_executor = ProviderActivationExecutor(real=RealProviderExecutor())
_provider_pipeline = ExecutionPipeline(executor=_provider_executor)
_execution_engine = ExecutionEngine(
    runtime=ExecutionRuntime(pipeline=_provider_pipeline)
)


def _build_preview_request(view: PreviewRequestView):
    """Bangun ExecutionRequest(mode='preview'). Provider tidak dieksekusi."""
    return ExecutionRequest(
        execution_id=view.execution_id,
        provider_id=view.provider_id,
        operation=view.operation,
        mode="preview",  # preview-only (ADR-024); bukan execute
    )


def _execute_preview(request: ExecutionRequest):
    """Eksekusi preview via ExecutionRuntime (tidak execute nyata)."""
    return _execution_engine.execute(request)


preview_gateway = wire_execution_preview(
    runtime_api,
    build_request=_build_preview_request,
    execute=_execute_preview,
)

# --- Session 02: Conversation -> RuntimeService -> ExecutionRuntime (preview) ---
# ConversationPreviewGateway memakai RuntimeAPI(execution.preview) yang sama
# (reuse Session 01). Builder ConversationExecutionContext -> ExecutionRequest
# mode=preview; payload HANYA namespace 'conversation' (AD-S02-001).
# Provider TIDAK dieksekusi (ADR-024 preview-only).
conversation_preview_gateway = ConversationPreviewGateway(runtime_api)
conversation_preview_gateway.configure(provider_id="filesystem")

# --- Session 05 (AD-S05): Knowledge consumer pertama via jalur resmi ---
# A: Wire Knowledge consumer di entry, pakai KnowledgeRegistry + Conversation
# KnowledgeBridge yang SUDAH ADA (tanpa ubah ExecutionRuntime/RuntimeService).
# B: Conversation meminta knowledge dgn namespace 'knowledge' di payload
# (AD-S02-001 forward compat). Memory diaktifkan bila registry didukung.
_knowledge_registry = KnowledgeRegistry()
knowledge_consumer = KnowledgePreviewConsumer(
    knowledgeregistry=_knowledge_registry,
)
# consumer memakai runtime_api (jalur resmi) utk preview; knowledge di-resolve
# via bridge di layer consumer (BUKAN pipeline internal).

# --- Session 06 (AD-S06): Workflow consumer pertama via jalur resmi ---
# Wire Workflow di entry, pakai WorkflowRegistry + ConversationWorkflowBridge /
# ConversationIntegrationBridge yg SUDAH ADA (tanpa ubah ExecutionRuntime/Service).
_workflow_registry = WorkflowRegistry()
workflow_consumer = WorkflowPreviewConsumer(registry=_workflow_registry)

# --- Session 07 (AD-S07): Artifact consumer pertama via Activation Pattern Std ---
# Conversation -> RuntimeService -> ExecutionRuntime(preview) -> ArtifactPreviewConsumer
# -> ArtifactRegistry -> ConversationArtifactBridge -> STOP (AD-ENG-002).
_artifact_registry = ArtifactRegistry()
artifact_consumer = ArtifactPreviewConsumer(registry=_artifact_registry)

# --- Session 08 (AD-S08): Memory consumer mandiri via Activation Pattern Std ---
# Conversation -> RuntimeService -> ExecutionRuntime(preview) -> MemoryPreviewConsumer
# -> MemoryRegistry -> ConversationMemoryBridge -> STOP (AD-ENG-002).
# MEMORY JADI CAPABILITY MANDIRI (bukan lagi namespace payload / hook pasif S05).
_memory_registry = MemoryRegistry()
memory_consumer = MemoryPreviewConsumer(registry=_memory_registry)

# --- Session 09 (AD-S09): Policy & Audit consumer via Activation Pattern Std ---
# Policy -> PolicyRegistry -> ConversationPolicyBridge -> STOP.
# Audit  -> AuditRegistry  -> ConversationAuditBridge  -> STOP. (AD-ENG-002)
# Policy & Audit tetap INDEPENDEN (tidak saling tahu implementasi).
_policy_registry = PolicyRegistry()
policy_consumer = PolicyPreviewConsumer(registry=_policy_registry)
_audit_registry = AuditRegistry()
audit_consumer = AuditPreviewConsumer(registry=_audit_registry)


@app.get("/")
async def index(request: Request):
    """Dashboard utama."""
    state = coordinator.state.value
    healthy = state in ("ready", "running", "healthy")
    health_str = "HEALTHY" if healthy else "DEGRADED"
    # WebRuntimeService: status lifecycle service (consumer RuntimeService).
    service_status = runtime_service.status_dict()
    # Session 04: Presentation Layer memakai jalur resmi (Runtime Status via DI).
    presentation_status = presentation_layer.runtime_status()
    # Fix (S10): web metrics kompatibel template (bugfix pre-existing).
    metrics = _web_metrics()

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
        "presentation": presentation_status,
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
    # Fix (S10): TelemetryService tidak punya get_metrics; gunakan get_stats.
    metrics = _web_metrics()
    adapter_name = coordinator.adapter_name
    # WebRuntimeService: lifecycle & contract untuk Runtime endpoint.
    service_status = runtime_service.status_dict()
    # Session 04: Presentation Layer Runtime Status via jalur resmi.
    presentation_status = presentation_layer.runtime_status()

    return templates.TemplateResponse("runtime.html", {
        "request": request,
        "state": state.upper(),
        "hosting": adapter_name,
        "runtime_service": service_status,
        "presentation": presentation_status,
        "metrics": metrics,
        "workspace": coordinator.workspace_path,
        "autonomous": coordinator.autonomous_enabled,
    })


@app.get("/workflow")
async def workflow_page(request: Request):
    """Workflow monitor — data dari WorkflowRegistry via consumer (bukan hardcode)."""
    workflow_ids = workflow_consumer.list_workflows()
    workflows = []
    for wf_id in workflow_ids:
        preview = workflow_consumer.resolve_workflow(wf_id)
        data = preview.as_dict()
        workflows.append({
            "id": data["workflow_id"],
            "name": data["name"],
            "status": data["status"] or "registered",
            "progress": 0,  # bukan bagian contract preview; nilai tampilan
        })
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
