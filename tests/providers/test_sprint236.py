"""Test Sprint 236 — Connector Runtime Integration (Program A).
Bridge read-only antara Connector Runtime (legacy) dan ProviderIntegration.
Tidak mengubah legacy. Preview-only, external_calls=0.
"""
import pytest

from sam.providers.connector_bridge.connector_bridge import (
    ConnectorProviderBridge,
    ConnectorProviderLink,
    ConnectorReadynessReport,
)
from sam.providers.integration.runtime_integration import ProviderIntegration
from sam.providers.openai import OpenAIAdapter
from sam.providers.ollama import OllamaAdapter

from sam.connectors.connector_registry import ConnectorRegistry
from sam.connectors.connector_descriptor import ConnectorDescriptor
from sam.connectors.connector_capability import ConnectorCapability
from sam.connectors.runtime import ConnectorRuntime

FROZEN_DTOS = [ConnectorProviderLink, ConnectorReadynessReport]


def build_connector_runtime():
    reg = ConnectorRegistry()
    reg.register(
        ConnectorDescriptor(
            connector_id="openai",
            name="OpenAI",
            connector_type="llm",
            version="1.0.0",
        )
    )
    reg.register(
        ConnectorDescriptor(
            connector_id="ollama",
            name="Ollama",
            connector_type="llm",
            version="1.0.0",
        )
    )
    reg.attach_capability(
        ConnectorCapability(
            capability_id="openai.chat",
            connector_id="openai",
            name="chat",
        )
    )
    return ConnectorRuntime(reg)


class TestConnectorProviderBridge:
    def test_link_matching_providers(self):
        runtime = build_connector_runtime()
        bridge = ConnectorProviderBridge(
            runtime, provider_ids=("openai", "ollama", "gemini"),
        )
        links = bridge.links()
        by_id = {l.connector_id: l for l in links}
        assert by_id["openai"].linked is True
        assert by_id["ollama"].linked is True
        assert by_id["openai"].external_calls == 0

    def test_report_ready(self):
        runtime = build_connector_runtime()
        bridge = ConnectorProviderBridge(
            runtime, provider_ids=("openai", "ollama"),
        )
        rep = bridge.report()
        assert rep.ready is True
        assert rep.connector_count == 2
        assert rep.provider_count == 2

    def test_connector_readiness(self):
        runtime = build_connector_runtime()
        bridge = ConnectorProviderBridge(runtime, provider_ids=("openai",))
        rd = bridge.connector_readiness()
        assert rd.ready is True

    def test_empty_report_not_ready(self):
        reg = ConnectorRegistry()
        bridge = ConnectorProviderBridge(ConnectorRuntime(reg), provider_ids=())
        rep = bridge.report()
        assert rep.ready is False
        assert rep.connector_count == 0

    def test_attach_providers(self):
        runtime = build_connector_runtime()
        bridge = ConnectorProviderBridge(runtime)
        assert bridge.report().provider_count == 0
        bridge.attach_providers(("openai",))
        assert bridge.report().provider_count == 1


class TestIntegrationWiring:
    def test_provider_integration_plus_bridge(self):
        # Simulasi wiring Program A penuh: ProviderIntegration -> Bridge.
        integration = ProviderIntegration()
        integration.register(OpenAIAdapter())
        integration.register(OllamaAdapter())

        runtime = build_connector_runtime()
        bridge = ConnectorProviderBridge(
            runtime, provider_ids=tuple(integration.list_providers()),
        )
        rep = bridge.report()
        assert rep.ready is True
        assert rep.provider_count == 2
        assert integration.has("openai")
        assert integration.has("ollama")


class TestBridgeImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
