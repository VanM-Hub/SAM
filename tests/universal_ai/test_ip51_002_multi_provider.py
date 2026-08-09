"""Test IP-5.1-002 - Multi Provider Integration (MISSION-5.1).

Coverage: WP-11..WP-20 - adapter framework, OpenAI/Anthropic/Google/Local
adapter, capability resolution, selection, failover assessment, compliance.
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "src")))

from sam.universal_ai import (
    AnthropicAdapter,
    CapabilityMapping,
    ConnectionStatus,
    FailoverAssessor,
    GoogleAIAdapter,
    LocalModelAdapter,
    OpenAIAdapter,
    ProviderAdapter,
    ProviderAdapterError,
    ProviderIntegrationComplianceChecker,
    ProviderRequest,
    ProviderResolution,
    ProviderSelector,
)


# ---------------------------------------------------------------------------
# WP-11 Provider Adapter Framework
# ---------------------------------------------------------------------------

class DummyAdapter(ProviderAdapter):
    provider_id = "dummy"
    provider_name = "Dummy"

    def invoke(self, request: ProviderRequest):
        return self._mk(request, "dummy-ok")

    def _mk(self, request, text):
        from sam.universal_ai import NormalizedResponse

        return NormalizedResponse(text=text, provider_id=self.provider_id, model_id=request.model_id)


class TestAdapterFramework:
    def test_connect_defaults_connected(self):
        adapter = DummyAdapter()
        assert adapter.connect() == ConnectionStatus.CONNECTED

    def test_connect_error_on_false(self):
        adapter = DummyAdapter()
        adapter.bind(lambda: False)
        assert adapter.connect() == ConnectionStatus.ERROR

    def test_map_error(self):
        adapter = DummyAdapter()
        err = adapter.map_error(ValueError("x"))
        assert isinstance(err, ProviderAdapterError)
        assert err.provider_id == "dummy"


# ---------------------------------------------------------------------------
# WP-12..15 Provider Adapters
# ---------------------------------------------------------------------------

class TestOpenAIAdapter:
    def test_mock_invoke(self):
        adapter = OpenAIAdapter()
        resp = adapter.invoke(ProviderRequest(provider_id="openai", prompt="hi", model_id="gpt"))
        assert resp.text == "openai-mock-response"
        assert resp.provider_id == "openai"

    def test_transport_invoke(self):
        adapter = OpenAIAdapter(transport=lambda p: {"choices": [{"message": {"content": "real"}}], "model": p["model"]})
        resp = adapter.invoke(ProviderRequest(provider_id="openai", prompt="hi", model_id="gpt"))
        assert resp.text == "real"

    def test_error_transport(self):
        def bad(_p):
            raise ValueError("cfg")

        adapter = OpenAIAdapter(transport=bad)
        try:
            adapter.invoke(ProviderRequest(provider_id="openai", prompt="hi"))
            assert False
        except ProviderAdapterError as exc:
            assert exc.code == "openai_error"


class TestAnthropicAdapter:
    def test_mock_invoke(self):
        resp = AnthropicAdapter().invoke(ProviderRequest(provider_id="anthropic", prompt="hi"))
        assert resp.text == "anthropic-mock-response"

    def test_transport(self):
        adapter = AnthropicAdapter(transport=lambda p: {"content": [{"text": "a"}], "model": "claude"})
        assert adapter.invoke(ProviderRequest(provider_id="anthropic", prompt="hi")).text == "a"


class TestGoogleAdapter:
    def test_mock_invoke(self):
        resp = GoogleAIAdapter().invoke(ProviderRequest(provider_id="google_ai", prompt="hi"))
        assert resp.text == "google-mock-response"

    def test_transport(self):
        adapter = GoogleAIAdapter(
            transport=lambda p: {"candidates": [{"content": {"parts": [{"text": "g"}]}}], "model": "gemini"}
        )
        assert adapter.invoke(ProviderRequest(provider_id="google_ai", prompt="hi")).text == "g"


class TestLocalAdapter:
    def test_mock_invoke(self):
        resp = LocalModelAdapter().invoke(ProviderRequest(provider_id="local_model", prompt="hi"))
        assert resp.text == "local-mock-response"

    def test_transport(self):
        adapter = LocalModelAdapter(transport=lambda p: {"response": "local", "model": "m"})
        assert adapter.invoke(ProviderRequest(provider_id="local_model", prompt="hi")).text == "local"


# ---------------------------------------------------------------------------
# WP-16 Capability Resolution
# ---------------------------------------------------------------------------

class TestCapabilityResolution:
    def test_mapping_supports(self):
        mapping = CapabilityMapping()
        from sam.universal_ai import AICapabilityKind

        mapping.declare("openai", "gpt", (AICapabilityKind.TEXT_GENERATION,))
        assert mapping.supports("openai", "gpt", AICapabilityKind.TEXT_GENERATION) is True
        assert mapping.unsupported("openai", "gpt", AICapabilityKind.VISION) is True


# ---------------------------------------------------------------------------
# WP-17 Provider Selection
# ---------------------------------------------------------------------------

class TestProviderSelection:
    def test_select_compatible(self):
        adapter = DummyAdapter()
        adapter.connect()
        selector = ProviderSelector(adapters=(adapter,))
        resolution = selector.select()
        assert isinstance(resolution, ProviderResolution)
        assert resolution.selected_provider_id == "dummy"
        assert resolution.resolved is True

    def test_select_respects_preference(self):
        a1, a2 = DummyAdapter(), DummyAdapter()
        a1.provider_id = "a"
        a2.provider_id = "b"
        selector = ProviderSelector(adapters=(a1, a2), preference=("b",))
        assert selector.select().selected_provider_id == "b"

    def test_select_none_when_no_adapter(self):
        assert ProviderSelector().select().resolved is False


# ---------------------------------------------------------------------------
# WP-18 Failover Assessment
# ---------------------------------------------------------------------------

class TestFailover:
    def test_recommend_alternative(self):
        primary = DummyAdapter()
        primary.provider_id = "primary"
        alt = DummyAdapter()
        alt.provider_id = "alt"
        alt.connect()
        primary.connect()
        assessor = FailoverAssessor(adapters=(primary, alt))
        # simulasi primary error status
        primary._status = ConnectionStatus.ERROR
        result = assessor.assess("primary")
        assert result.available is False
        assert result.recommendation == "use_alternative"
        assert len(result.candidates) == 1


# ---------------------------------------------------------------------------
# WP-19 Provider Integration Compliance
# ---------------------------------------------------------------------------

class TestIntegrationCompliance:
    def test_certify_passes(self):
        adapters = (OpenAIAdapter(), AnthropicAdapter(), GoogleAIAdapter(), LocalModelAdapter())
        cert = ProviderIntegrationComplianceChecker().certify(adapters)
        assert cert["certified"] is True

    def test_fails_on_sdk_leak(self):
        cert = ProviderIntegrationComplianceChecker().certify((OpenAIAdapter(),), no_sdk_leak=False)
        assert cert["certified"] is False


# ---------------------------------------------------------------------------
# WP-20 Integration
# ---------------------------------------------------------------------------

class TestMultiProviderIntegration:
    def test_adapters_registered(self):
        adapters = (OpenAIAdapter(), AnthropicAdapter(), GoogleAIAdapter(), LocalModelAdapter())
        assert len(adapters) == 4
        cert = ProviderIntegrationComplianceChecker().certify(adapters)
        assert cert["certified"] is True
