"""K6 - End-to-end verification jalur resmi (no network, no bypass).

Jalur yang dibuktikan TANPA bypass:
    Presentation (host) -> RuntimeService -> Connector Runtime
        -> Provider Runtime -> Agent Runtime

Pendekatan: jagalah urutan CHAIN lewat contract id yang SAMA di setiap layer
(`connector.llm.chat`), dan pastikan aliran data connector -> provider -> agent
BERJALAN melalui composition root resmi (bukan panggilan langsung ke layer
yang dilewati). Host tetap memakai RuntimeService (dibuktikan di K5); di sini
dibuktikan rantai Connector -> Provider -> Agent terhubung & dapat dieksekusi
(preview, external_calls=0 di jalur agent) tanpa mengubah RuntimeService.
"""
from sam.api.llm_wiring import (
    LLM_CONNECTOR_CONTRACT_ID,
    llm_connector_layer,
    llm_provider_layer,
    llm_agent_layer,
    llm_agent_bridge,
)

import asyncio


def _run(coro):
    """Jalankan coroutine deterministik (anti-flaky di Python 3.8)."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


class TestE2EChain:
    """Urutan Connector -> Provider -> Agent terhubung lewat contract id sama."""

    def test_contract_id_sama_diseluruh_layer(self) -> None:
        # Connector contract
        conn_contract = llm_connector_layer.registry.get_contract("llm_chat")
        assert conn_contract is not None
        assert conn_contract.contract_id == LLM_CONNECTOR_CONTRACT_ID
        # Provider implements
        for pid in ("openai", "anthropic", "gemini", "deepseek", "ollama"):
            desc = llm_provider_layer.registry.get(pid)
            assert desc is not None
            assert LLM_CONNECTOR_CONTRACT_ID in desc.implements
        # Agent implements
        agent_desc = llm_agent_layer.registry.get("mission_agent")
        assert agent_desc is not None
        assert LLM_CONNECTOR_CONTRACT_ID in agent_desc.implements

    def test_connector_readiness_ready(self) -> None:
        r = llm_connector_layer.readiness()
        assert r.ready is True

    def test_provider_layer_tersedia(self) -> None:
        assert llm_provider_layer.summary()["total_providers"] == 5

    def test_agent_layer_ready(self) -> None:
        assert llm_agent_layer.agent_ready() is True

    def test_chain_eksekusi_tanpa_bypass(self) -> None:
        """Alur data connector->provider->agent memakai wiring resmi.

        Provider (executor, adapter OpenAI) -> Agent (mission via MCR preview).
        Jalur agent tetap preview: external_calls SELALU 0.
        Ini membuktikan rantai terhubung, tanpa panggilan langsung yang
        melewati layer (bypass), dan tanpa mengubah RuntimeService.
        """
        # Rantai: connector aktif -> provider (via executor) -> agent (via bridge)
        res = _run(llm_agent_bridge.run_mission_cognitive("openai", "mis-k6-e2e"))
        assert res.ok is True
        assert res.final_state == "Completed"
        assert res.external_calls == 0  # jalur mission tetap preview-only

    def test_no_bypass_bukti_layer_saling_terhubung_via_contract(self) -> None:
        """Semua layer berbagi contract id -> rantai resmi, bukan paralel."""
        ids = set()
        ids.add(llm_connector_layer.registry.get_contract("llm_chat").contract_id)
        for pid in llm_provider_layer.list_providers():
            ids.update(llm_provider_layer.registry.get(pid).implements)
        ids.update(llm_agent_layer.registry.get("mission_agent").implements)
        assert LLM_CONNECTOR_CONTRACT_ID in ids
        # Provider & agent keduanya terikat ke contract yang sama (bukan paralel).
        assert all(i == LLM_CONNECTOR_CONTRACT_ID for i in ids)
