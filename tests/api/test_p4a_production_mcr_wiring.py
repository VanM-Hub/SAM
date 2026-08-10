"""P4A - Production MCR Wiring (Architecture Acceptance 2026-08-11).

Bukti responsibility-based migration (Skenario B - Refactor into Application Use Case):
    HTTP POST /mission/{id}
      -> AgentBridge.run_mission_cognitive(provider_id, mission_id)   [application boundary PRESERVED]
      -> MissionCognitiveRuntime.run_cycle(...)                        [single cognitive owner]
          -> Reason -> Plan(MissionBuilder) -> Govern(external) -> Execute(official)
          -> Observe(best-effort) -> Reflect(ReflectionManager) -> Learn
      -> AgentRunResult (kontrak REST dipre-serve, serializer tidak tahu internal MCR)

Guardrail yang diuji (Architecture Acceptance P4A):
- Single cognitive owner: jalur production memakai MCR; AgentRuntime TIDAK lagi
  orchestration owner jalur ini (tapi tetap ada, tidak dihapus - migration safety).
- MissionBuilder EXACTLY ONCE invocation pada satu request (MCR invoke, bukan AgentRuntime).
- REST contract compatibility: ok=True, final_state='Completed', external_calls=0.
- Governance eksternal via ApprovalGate (adapter kontrak; authority tetap kernel).
- Execution official path via GovernedExecution (preview: external_calls=0, no real exec).
- Observation read-only/best-effort (gagal/tanpa engine TIDAK menggagalkan siklus).
- Reflection via ReflectionManager (bukan SelfHealingLoop).
"""
import asyncio

from fastapi.testclient import TestClient

from sam.api.server import app
from sam.api.llm_wiring import llm_agent_bridge
from sam.mission_cognition import AgentRunResult, MissionCycleStatus


def _run(coro):
    """Jalankan coroutine deterministik (anti-flaky di Python 3.8).

    `asyncio.get_event_loop()` terpengaruh state global (setelah TestClient
    hidup/mati, loop bisa closed -> coroutine never awaited). Pakai event loop
    baru per pemanggilan agar deterministik & tidak bocor antar test.
    """
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


def _client() -> TestClient:
    return TestClient(app)


class TestP4ASingleCognitiveOwner:
    """AgentRuntime TIDAK lagi orchestration owner jalur production mission."""

    def test_production_route_memakai_MCR(self) -> None:
        """Route produksi memanggil run_mission_cognitive (bukan AgentRuntime path)."""
        import sam.api.routes.mission as mission_route
        src = open(mission_route.__file__, encoding="utf-8").read()
        assert "run_mission_cognitive" in src
        # Route TIDAK memakai AgentRuntime legacy orchestration.
        assert "run_mission_from_provider" not in src

    def test_bridge_menyuntikkan_MCR_single_owner(self) -> None:
        """AgentBridge memegang MissionCognitiveRuntime (bukan AgentRuntime sbg owner)."""
        from sam.mission_cognition import MissionCognitiveRuntime
        assert isinstance(llm_agent_bridge._mcr, MissionCognitiveRuntime)


class TestP4AExactlyOneMissionBuilder:
    """MissionBuilder di-invoke EXACTLY ONCE per request (langkah 5)."""

    def test_satu_invocation_mission_builder_per_cycle(self) -> None:
        import sam.agent.planner.mission_builder as mb

        class _Spy:
            def __init__(self):
                self.calls = 0
                self._orig = None

            def install(self):
                self._orig = mb.MissionBuilder.build_default

                def wrapper(self_builder, plan_id, mission_id):
                    self.calls += 1
                    return self._orig(self_builder, plan_id, mission_id)

                mb.MissionBuilder.build_default = wrapper

            def restore(self):
                mb.MissionBuilder.build_default = self._orig

        spy = _Spy()
        spy.install()
        try:
            res = _run(llm_agent_bridge.run_mission_cognitive("openai", "p4a-single"))
        finally:
            spy.restore()
        assert res.ok is True
        assert spy.calls == 1, (
            "MissionBuilder harus di-invoke EXACTLY ONCE per request "
            f"(MCR invoke; AgentRuntime TIDAK boleh invoke lagi) - calls={spy.calls}"
        )


class TestP4ARESTContractCompatibility:
    """Kontrak REST dipertahankan (langkah 6) - route & serializer tidak berubah."""

    def test_http_post_kontrak_kompatibel(self) -> None:
        client = _client()
        resp = client.post("/mission/p4a-rest-1", json={"provider_id": "openai"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["mission_id"] == "p4a-rest-1"
        assert data["ok"] is True
        assert data["final_state"] == "Completed"
        assert data["external_calls"] == 0, "preview-only: external_calls must be 0"

    def test_return_type_agent_run_result(self) -> None:
        res = _run(llm_agent_bridge.run_mission_cognitive("openai", "p4a-type"))
        assert isinstance(res, AgentRunResult)
        assert res.final_state == "Completed"

    def test_serializer_tidak_perlu_tahu_internal_mcr(self) -> None:
        """Route memetakan AgentRunResult (bukan MissionCycleResult) ke REST."""
        import sam.api.routes.mission as mission_route
        src = open(mission_route.__file__, encoding="utf-8").read()
        # Serializer membaca field AgentRunResult (mission_id/ok/final_state/...).
        assert "final_state" in src
        # Route TIDAK import/know internal MCR classes.
        assert "mission_cognition" not in src


class TestP4AGuardrails:
    """Governance eksternal, execution official, observation, reflection (langkah 7)."""

    def test_governance_dieksternal_via_approval_gate(self) -> None:
        """MCR memakai governance eksternal (adapter ApprovalGate), TIDAK logic sendiri."""
        gov = llm_agent_bridge._mcr._governance_engine
        assert gov is not None, "governance engine wajib disuntikkan (harus eksternal)"
        from sam.api.llm_wiring import _MissionGovernanceAdapter
        assert isinstance(gov, _MissionGovernanceAdapter)

    def test_execution_official_path_preview(self) -> None:
        """MCR memakai execution official (GovernedExecution), preview, no real exec."""
        exec_rt = llm_agent_bridge._mcr._execution_runtime
        assert exec_rt is not None
        from sam.execution_runtime.governed_execution import GovernedExecution
        assert isinstance(exec_rt, GovernedExecution)
        # Preview: external_calls tetap 0 (ADR-008 sec 12).
        res = _run(llm_agent_bridge.run_mission_cognitive("openai", "p4a-guard-exec"))
        assert res.external_calls == 0

    def test_observation_read_only_best_effort(self) -> None:
        """Tanpa observation engine, siklus TETAP COMPLETED (bukan gagal/block)."""
        res = _run(llm_agent_bridge.run_mission_cognitive("openai", "p4a-guard-obs"))
        assert res.ok is True  # observe never govern: tanpa engine tetap lanjut

    def test_reflection_via_reflection_manager(self) -> None:
        """MCR memakai ReflectionManager (healing), bukan SelfHealingLoop."""
        from sam.healing.reflection import ReflectionManager
        assert isinstance(llm_agent_bridge._mcr._reflection_manager, ReflectionManager)
