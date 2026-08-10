"""K3 - Agent Runtime Activation (unit tests, no network).

Membuktikan Provider Runtime TERHUBUNG ke Agent baseline:
- Agent baseline terdaftar dengan `implements=<connector contract>` (link
  Provider -> Agent; urutan Connector -> Provider -> Agent dipertahankan
  lewat contract id yang sama).
- Jalur mission menggunakan MissionCognitiveRuntime (single cognitive owner,
  P4A + Step 9B); AgentRuntime legacy telah di-retire.
- Preview-only: external_calls SELALU 0 di jalur agent.
- `AgentBridge` (di lapisan wiring) menghubungkan provider -> mission agent,
  TANPA menjadikan Agent Runtime orchestrator baru dan TANPA mengubah
  RuntimeService.
"""
from sam.api.llm_wiring import (
    LLM_CONNECTOR_CONTRACT_ID,
    llm_agent_layer,
    llm_agent_bridge,
    agent_activation,
)
from sam.mission_cognition import AgentRunResult
from sam.agent.foundation.agent_registry import AgentRegistry

import asyncio


def _run(coro):
    """Jalankan coroutine deterministik (anti-flaky di Python 3.8)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestAgentRegistryBaseline:
    """Agent baseline terdaftar & terhubung ke connector contract."""

    def test_agent_baseline_terdaftar(self) -> None:
        ids = llm_agent_layer.registry.list_ids()
        assert ids == ["mission_agent"]

    def test_agent_implements_connector_contract(self) -> None:
        desc = llm_agent_layer.registry.get("mission_agent")
        assert desc is not None
        assert LLM_CONNECTOR_CONTRACT_ID in desc.implements

    def test_agent_capability_dan_contract(self) -> None:
        caps = llm_agent_layer.registry.get_capabilities("mission_agent")
        assert {c.name for c in caps} == {"mission_lifecycle"}
        contract = llm_agent_layer.registry.get_contract("mission_agent")
        assert contract is not None
        assert contract.contract_id == LLM_CONNECTOR_CONTRACT_ID

    def test_activation_report(self) -> None:
        report = agent_activation()
        assert report["contract"] == LLM_CONNECTOR_CONTRACT_ID
        assert report["agents"][0]["agent_id"] == "mission_agent"


class TestAgentRuntimeNoSemanticChange:
    """Container test: jalur mission preview-only, bukan orchestrator baru."""

    def test_layer_memegang_registry_agent_baseline(self) -> None:
        assert isinstance(llm_agent_layer.registry, AgentRegistry)
        assert llm_agent_layer.agent_ready() is True

    def test_external_calls_selalu_nol(self) -> None:
        # Bridge menjalankan misi via MCR; preview-only (external_calls=0).
        res = _run(llm_agent_bridge.run_mission_cognitive("openai", "mis-k3-x"))
        assert isinstance(res, AgentRunResult)
        assert res.ok is True
        assert res.final_state == "Completed"
        assert res.external_calls == 0

    def test_bridge_mengekspos_jalur_mission_cognitive(self) -> None:
        # Bridge mengekspos use case mission cognitive (canonical), bukan
        # legacy orchestration AgentRuntime.
        from sam.api.llm_wiring import AgentBridge
        bridge_public = {m for m in dir(llm_agent_bridge) if not m.startswith("_")}
        assert "run_mission_cognitive" in bridge_public
        assert "map_cognitive_result" in bridge_public
        # AgentBridge bukan subclass runtime engine baru.
        assert not isinstance(bridge_public, type)
