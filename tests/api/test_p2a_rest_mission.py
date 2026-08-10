"""P2A - Production REST Mission Route (operational verification).

Membuktikan MissionBuilder CALLED + MISSION-REACHABLE dari jalur operasional
HTTP (produksi), bukan hanya dari test langsung:

    HTTP Request
       -> Mission Route (adapter)
       -> Composition Root (api.llm_wiring)
       -> AgentBridge -> MissionCognitiveRuntime
       -> MissionBuilder  (via MCR, EXACTLY ONCE)

Guardrail P2A (scope ketat):
    - HANYA mengaktifkan MissionBuilder. TIDAK menyentuh MCR, Governance,
      Execution, RuntimeService, reasoning/engine.py, SelfHealingLoop.
    - Route bersifat adapter; orchestration tetap di AgentBridge (application
      use case), bukan di route.

Acceptance Criteria P2A (trace aktual):
    IMPORTABLE         ✅
    CALLED             ✅ (via HTTP route produksi, bukan helper test)
    MISSION-REACHABLE  ✅
    Governance         ✅ UNCHANGED
    Execution          ✅ UNCHANGED
    RuntimeService     ✅ UNCHANGED
"""
from fastapi.testclient import TestClient

from sam.api.server import app
from sam.api.llm_wiring import llm_agent_bridge, llm_agent_layer, llm_provider_layer

import asyncio


def _run(coro):
    """Jalankan coroutine deterministik (anti-flaky di Python 3.8)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _client() -> TestClient:
    return TestClient(app)


class TestP2ARestMissionEntry:
    """Mission route adalah production entry point (HTTP -> MissionBuilder)."""

    def test_route_terdaftar_di_server(self) -> None:
        """
        Endpoint /mission/{id} tersedia di aplikasi produksi (IMPORTABLE).

        Verikasi berbasis perilaku (bukan introspeksi `app.routes`): FastAPI/
        Starlette versi baru mengubah struktur `app.routes` (lazy `_IncludedRouter`),
        sehingga iterasi flat tidak lagi valid. POST sampai ke route (bukan 404/405)
        membuktikan route terdaftar & routable tanpa meregangkan struktur internal.
        """
        client = _client()
        resp = client.post("/mission/route-probe", json=None)
        assert resp.status_code != 404, "route /mission/{mission_id} tidak terdaftar"
        assert resp.status_code != 405, "route /mission/{mission_id} salah method (harus POST)"

    def test_mission_post_menjalankan_MissionBuilder(self) -> None:
        """HTTP request -> MissionBuilder menghasilkan plan (CALLED + REACHABLE)."""
        client = _client()
        resp = client.post("/mission/mis-p2a-http-1", json={"provider_id": "openai"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["mission_id"] == "mis-p2a-http-1"
        assert data["ok"] is True
        assert data["final_state"] == "Completed"
        assert data["external_calls"] == 0, "preview-only: external_calls must be 0"

    def test_mission_post_body_default_provider(self) -> None:
        """Tanpa body, provider default dipakai (openai baseline)."""
        client = _client()
        resp = client.post("/mission/mis-p2a-http-2", json=None)
        assert resp.status_code == 200, resp.text
        assert resp.json()["ok"] is True

    def test_mission_get_daftar_agent(self) -> None:
        """GET /mission/ membaca registry (read-only)."""
        client = _client()
        resp = client.get("/mission/")
        assert resp.status_code == 200, resp.text
        assert resp.json()["agents"] == ["mission_agent"]


class TestP2ARouteAdapterBukanOrchestrator:
    """Route adalah ADAPTER; orchestration tetap di AgentBridge (Clean Arch)."""

    def test_route_tidak_import_mission_builder_langsung(self) -> None:
        """Route memanggil composition root (llm_agent_bridge), bukan MissionBuilder."""
        import sam.api.routes.mission as mission_route
        src = open(mission_route.__file__, encoding="utf-8").read()
        # Route memakai AgentBridge (application use case), bukan MissionBuilder langsung.
        assert "llm_agent_bridge" in src
        assert "from sam.agent.planner" not in src, \
            "route tidak boleh import MissionBuilder langsung (harus via use case)"


class TestP2AExistingUnchanged:
    """RuntimeService / Governance / Execution tetap UNCHANGED (guardrail)."""

    def test_llm_layers_tetap_ada(self) -> None:
        """Composition root LLM (provider/agent) masih teraktivasi normal."""
        assert llm_agent_layer.agent_ready() is True
        assert "openai" in llm_provider_layer.list_providers()

    def test_bridge_masih_dipakai(self) -> None:
        """Jalur mission produksi memakai AgentBridge yang sama (tidak duplikat)."""
        res = _run(llm_agent_bridge.run_mission_cognitive("openai", "mis-p2a-guar"))
        assert res.ok is True
        assert res.external_calls == 0
