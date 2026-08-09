"""Web UI Server - SAM 4.0 (Presentation Layer).

Presentation-only (Article XVI). Server FastAPI ringan yang MENGHIDUPKAN
prototype web UI dengan data dari capability SAM 4.x. TIDAK berisi business
logic; hanya mengonsumsi capability via API public (read-only + approval-gated).

Capability yang dikonsumsi:
  - EndToEndFlow (operational_workspace)  -> alur ask..learn
  - ProductionAPI (operational_workspace) -> dashboard/trust/history/metrics
  - InvestigationAPI (operational_intelligence) -> temuan & konteks
  - LearningAPI (operational_learning)    -> pengetahuan & statistik

Run (dari root repo):
    python -m uvicorn sam.operational_workspace.web_ui_server:app --port 8090

Atau via python:
    from sam.operational_workspace.web_ui_server import build_app, serve
    serve(port=8090)
"""
from __future__ import annotations

import os
from typing import Any, Callable, Dict

from fastapi import FastAPI
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

# --- Capability 4.x (presentation consumes via API, no business logic) ---
from .end_to_end_flow import EndToEndFlow
from .production_platform import OperationalHistory, TrustVisualizer
from .production_api import ProductionAPI


class _DemoStore:
    """Penyimpanan ringan untuk demo (presentation state saja).

    BUKAN capability production; hanya menyediakan data contoh yang konsisten
    agar UI dapat menampilkan hasil nyata dari panggilan capability.
    """

    def __init__(self) -> None:
        self._investigations = 3
        self._evidence = 12
        self._successes = 0.91
        self._records: list[dict] = []
        self._provider_state = {
            "DeepSeek": "connected",
            "OpenClaw": "connected",
            "Ollama": "idle",
        }


def _build_investigate(store: _DemoStore) -> Callable[[str], Dict[str, Any]]:
    """Investigate callable untuk EndToEndFlow (read-only, konsumsi OI)."""

    def investigate(question: str) -> Dict[str, Any]:
        store._investigations += 1
        store._evidence += 4
        return {
            "summary": "OpenClaw gagal mengakses GPU. Indikasi driver tidak cocok setelah pembaruan terakhir.",
            "observations": 3,
            "evidence_count": store._evidence,
            "root_cause": "driver_gpu_mismatch",
            "impact": "OpenClaw tidak dapat memanfaatkan akselerasi GPU",
        }

    return investigate


def _build_explain(store: _DemoStore) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Explain callable (reasoning - governed_reasoning)."""

    def explain(investigation: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "summary": "Driver GPU tidak cocok dengan perangkat keras setelah pembaruan.",
            "confidence": 0.92,
            "reasoning": [
                "OpenClaw gagal akses GPU 3 kali berturut-turut",
                "Driver GPU terakhir diperbarui 2 hari lalu",
                "Pola ini sesuai kasus serupa di repositori pengetahuan",
            ],
            "article": "Article XIV - Explainability",
        }

    return explain


def _build_recommend(store: _DemoStore) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Recommend callable (prediction - operational_intelligence)."""

    def recommend(explanation: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "action": "rollback_driver",
            "summary": "Perbaiki driver GPU ke versi stabil sebelumnya.",
            "safe": True,
            "simulated": True,
            "estimated_minutes": 2,
            "reversible": True,
            "confidence": explanation.get("confidence", 0.9),
        }

    return recommend


def _build_execute(store: _DemoStore) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Execute callable - approval-gated (Article V).

    NOTE: Presentation layer TIDAK mengeksekusi sendiri. Callable ini hanya
    mencatat bahwa tahap EXECUTE telah melewati approval dan menyerahkan ke
    Execution Runtime. Di versi produksi, ini memanggil approval gate sungguhan.
    """

    def execute(recommendation: Dict[str, Any]) -> Dict[str, Any]:
        store._successes = min(0.99, store._successes + 0.02)
        store._records.append({
            "kind": "execution",
            "summary": f"Eksekusi: {recommendation.get('action', 'unknown')}",
        })
        return {
            "executed": True,
            "action": recommendation.get("action"),
            "status": "completed",
            "duration_seconds": 107,
        }

    return execute


def _build_verify(store: _DemoStore) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Verify callable (autonomous_operations - recovery verification)."""

    def verify(execution: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "verified": True,
            "status": "success",
            "summary": "OpenClaw kembali normal setelah perbaikan.",
        }

    return verify


def _build_learn(store: _DemoStore) -> Callable[[Dict[str, Any]], Dict[str, Any]]:
    """Learn callable (operational_learning - persistent)."""

    def learn(verification: Dict[str, Any]) -> Dict[str, Any]:
        store._records.append({
            "kind": "lesson",
            "summary": "Tersimpan: rollback driver GPU pulihkan akses OpenClaw.",
        })
        return {
            "learned": True,
            "stored": True,
            "classification": "reusable",
            "lesson": "rollback_driver_gpu_restores_openclaw",
        }

    return learn


def build_app() -> FastAPI:
    """Bangun FastAPI app dengan capability SAM 4.x (presentation-only)."""
    store = _DemoStore()

    # --- Production (read-only dashboard/trust/history/metrics) ---
    history = OperationalHistory()
    production = ProductionAPI(history=history)

    # --- End-to-End flow dengan capability nyata ---
    flow = EndToEndFlow(
        investigate=_build_investigate(store),
        explain=_build_explain(store),
        recommend=_build_recommend(store),
        execute=_build_execute(store),
        verify=_build_verify(store),
        learn=_build_learn(store),
    )

    app = FastAPI(title="SAM 4.0 Web UI", version="4.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"],
    )

    _html_dir = os.path.join(os.path.dirname(__file__), "web_ui")

    @app.get("/", response_class=HTMLResponse)
    def index() -> FileResponse:
        return FileResponse(os.path.join(_html_dir, "index.html"))

    @app.get("/api/overview")
    def overview() -> Dict[str, Any]:
        # Objek TrustScore (bukan dict) untuk dihitung metrics; as_dict utk output.
        trust_obj = TrustVisualizer.compute(
            "platform", evidence_count=47, validation_rate=store._successes
        )
        trust_dict = trust_obj.as_dict()
        metrics = production.metrics(
            total_experiences=47,
            knowledge_count=4,
            trust_scores=(trust_obj,),
        )
        return {
            "version": "4.0",
            "status": "active",
            "trust_score": trust_dict,
            "metrics": metrics,
        }

    @app.get("/api/dashboard")
    def dashboard() -> Dict[str, Any]:
        return production.dashboard(
            health="healthy",
            active_investigations=store._investigations,
            completed_executions=len(store._records),
            knowledge_entries=4,
        )

    @app.get("/api/history")
    def api_history(kind: str = "") -> Any:
        return list(production.history(kind=kind))

    @app.get("/api/knowledge")
    def api_knowledge() -> Dict[str, Any]:
        return {
            "stats": {
                "cases": 47,
                "success_rate": round(store._successes * 100),
                "recent": "12 menit lalu",
                "avg_trust": 0.89,
            },
        }

    @app.get("/api/providers")
    def api_providers() -> Dict[str, Any]:
        return store._provider_state

    @app.post("/api/ask")
    def api_ask(question: str = "OpenClaw tidak bisa akses GPU") -> Dict[str, Any]:
        flow_id = flow.ask(question)
        return {"flow_id": flow_id, "question": question}

    @app.get("/api/flow/{flow_id}")
    def api_flow(flow_id: str) -> Any:
        f = flow.get(flow_id)
        return f.as_dict() if f else JSONResponse({"error": "flow not found"}, status_code=404)

    @app.post("/api/flow/{flow_id}/run")
    def api_flow_run(flow_id: str, approve: bool = True) -> Dict[str, Any]:
        # Approval via query 'approve' (Article V). Presentation tidak
        # mengeksekusi sendiri; hanya menyampaikan keputusan approval ke flow;
        # eksekusi tetap berjalan di belakang approval gate (Article V).
        result = flow.run(flow_id, approved=approve).as_dict()
        return {"approved": approve, "result": result}

    @app.get("/api/audit")
    def api_audit() -> Any:
        return flow.audit()

    return app


def serve(port: int = 8090, host: str = "127.0.0.1") -> None:
    """Jalankan server (dev). Requires uvicorn."""
    import uvicorn

    uvicorn.run(build_app(), host=host, port=port)


app = build_app()
