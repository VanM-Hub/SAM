"""K1 - Connector Runtime Activation (unit tests, no network).

Membuktikan layer Connector Runtime baseline AKTIF setelah wiring Program K:
- Connector baseline LLM terdaftar di ConnectorRegistry.
- ConnectorRuntime readiness PASS (registry + capability + binding).
- Contract connector tersedia (dijadikan link Provider -> Connector).
- Tidak ada semantic change: ConnectorRuntime tetap preview-only (tidak ada
  eksekusi provider / tidak ada network).
"""
import pytest

from sam.api.llm_wiring import (
    LLM_CONNECTOR_CONTRACT_ID,
    llm_connector_layer,
    connector_readiness,
)
from sam.connectors import ConnectorRuntime, ConnectorRegistry


class TestLLMConnectorLayerComposition:
    """Composition root K1 - connector baseline terdaftar & runtime aktif."""

    def test_connector_baseline_daftar(self) -> None:
        registry = llm_connector_layer.registry
        assert registry.count() == 1
        assert registry.list_ids() == ["llm_chat"]
        desc = registry.get("llm_chat")
        assert desc is not None
        assert desc.connector_type == "llm"

    def test_capability_dan_contract_terkait(self) -> None:
        registry = llm_connector_layer.registry
        caps = registry.get_capabilities("llm_chat")
        assert len(caps) == 2
        assert {c.name for c in caps} == {"chat", "model_list"}
        contract = registry.get_contract("llm_chat")
        assert contract is not None
        assert contract.contract_id == LLM_CONNECTOR_CONTRACT_ID

    def test_runtime_adalah_ConnectorRuntime_yang_ada(self) -> None:
        # Wajib re-use engine yang SUDAH ADA, bukan kelas baru.
        assert isinstance(llm_connector_layer.runtime, ConnectorRuntime)

    def test_registry_adalah_ConnectorRegistry_yang_ada(self) -> None:
        assert isinstance(llm_connector_layer.registry, ConnectorRegistry)


class TestLLMConnectorReadiness:
    """Readiness Connector Runtime setelah aktivasi."""

    def test_readiness_pass(self) -> None:
        r = llm_connector_layer.readiness()
        assert r.ready is True
        stages = {c.stage for c in r.checks}
        assert {"registry", "capability", "binding"}.issubset(stages)

    def test_connector_readiness_report(self) -> None:
        report = connector_readiness()
        assert report["ready"] is True
        assert len(report["checks"]) == 3

    def test_summary_menunjukan_1_connector_llm(self) -> None:
        s = llm_connector_layer.summary()
        assert s["total_connectors"] == 1
        assert s["registered"] == 1
        assert s["by_type"] == {"llm": 1}
        assert s["contract"] == LLM_CONNECTOR_CONTRACT_ID


class TestNoSemanticChange:
    """Guardrail: tidak ada semantic change pada Connector Runtime.

    Connector Runtime tetap preview-only: tidak mengeksekusi provider,
    tidak melakukan network, external_calls selalu 0.
    """

    def test_connector_runtime_tidak_memiliki_jalur_eksekusi_provider(self) -> None:
        # ConnectorRuntime baseline hanya read registry/summary; tidak ada
        # method execute/call provider. Ini memastikan tidak ada semantic change.
        runtime = llm_connector_layer.runtime
        public = {m for m in dir(runtime) if not m.startswith("_")}
        assert not ({"execute", "call", "run_provider"}.intersection(public))

    def test_registry_tetap_deterministik_preview_only(self) -> None:
        # Tidak ada network/async di registry connector baseline.
        registry = llm_connector_layer.registry
        public = {m for m in dir(registry) if not m.startswith("_")}
        assert not ({"execute", "call", "connect", "stream"}.intersection(public))
