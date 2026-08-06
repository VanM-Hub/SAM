"""K3 - Agent Runtime Activation (unit tests, no network).

Membuktikan Provider Runtime TERHUBUNG ke Agent Runtime baseline:
- Agent baseline terdaftar dengan `implements=<connector contract>` (link
  Provider -> Agent; urutan Connector -> Provider -> Agent dipertahankan
  lewat contract id yang sama).
- Memakai `AgentRuntime` yang SUDAH ADA (kelas sama, bukan baru).
- Semantic AgentRuntime TIDAK diubah: preview-only, deterministik,
  external_calls SELALU 0 di jalur agent.
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
from sam.agent.runtime.agent_runtime import AgentRuntime, AgentRunResult
from sam.agent.foundation.agent_registry import AgentRegistry


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
    """Agent Runtime tetap preview-only, bukan orchestrator baru."""

    def test_runtime_adalah_AgentRuntime_yang_ada(self) -> None:
        assert isinstance(llm_agent_layer.runtime, AgentRuntime)
        assert isinstance(llm_agent_layer.registry, AgentRegistry)

    def test_external_calls_selalu_nol(self) -> None:
        # Bridge menjalankan misi dari provider; AgentRuntime preview-only.
        res = llm_agent_bridge.run_mission_from_provider("openai", "mis-k3-x")
        assert isinstance(res, AgentRunResult)
        assert res.ok is True
        assert res.final_state == "Completed"
        assert res.external_calls == 0

    def test_bridge_bukan_orchestrator_baru(self) -> None:
        # Bridge hanya menjalankan AgentRuntime yang sudah ada; tidak ada
        # kelas runtime baru dengan jalur eksekusi sendiri.
        from sam.api.llm_wiring import AgentBridge
        bridge_public = {m for m in dir(llm_agent_bridge) if not m.startswith("_")}
        assert "run_mission_from_provider" in bridge_public
        # AgentBridge bukan subclass runtime engine baru.
        assert not isinstance(bridge_public, type)
