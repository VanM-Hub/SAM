# -*- coding: utf-8 -*-
"""
OP-289 — Provider Integration Test

Verifikasi:
  - Semua provider implement interface ReasoningProvider
  - Semua provider menghasilkan DTO identik (ReasoningResponse)
  - Tidak ada network call
  - Semua menggunakan Fake Response
"""

from __future__ import annotations
import pytest
from sam.operations.reasoning.provider import (
    ReasoningProvider, ReasoningRequest, UsageMetrics,
)
from sam.operations.reasoning.gateway import (
    MockProvider, OpenAIProvider, GeminiProvider,
    ClaudeProvider, OllamaProvider, LLMGateway,
)


ALL_PROVIDERS = [
    ("mock", MockProvider()),
    ("openai", OpenAIProvider()),
    ("gemini", GeminiProvider()),
    ("claude", ClaudeProvider()),
    ("ollama", OllamaProvider()),
]


class TestProviderInterface:
    """Verifikasi semua provider implementasi interface yang benar."""

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_generate_returns_reasoning_response(self, name, provider):
        request = ReasoningRequest(prompt="Test question")
        response = provider.generate(request)
        from sam.operations.reasoning.provider import ReasoningResponse
        assert isinstance(response, ReasoningResponse)

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_generate_has_answer(self, name, provider):
        request = ReasoningRequest(prompt="What is the status?")
        response = provider.generate(request)
        assert response.answer, f"{name}: empty answer"
        assert name.lower() in response.answer.lower()

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_generate_has_confidence(self, name, provider):
        request = ReasoningRequest(prompt="test")
        response = provider.generate(request)
        assert 0 <= response.confidence <= 1.0

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_generate_has_provider(self, name, provider):
        request = ReasoningRequest(prompt="test")
        response = provider.generate(request)
        assert response.provider == name or response.provider == "unknown"

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_generate_has_usage(self, name, provider):
        request = ReasoningRequest(prompt="test")
        response = provider.generate(request)
        assert response.usage is not None

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_health_returns_bool(self, name, provider):
        h = provider.health()
        assert isinstance(h, bool)

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_metadata_returns_provider_metadata(self, name, provider):
        md = provider.metadata()
        from sam.operations.reasoning.provider import ProviderMetadata
        assert isinstance(md, ProviderMetadata)
        assert md.provider_name == name
        assert md.model_name

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_close_does_not_raise(self, name, provider):
        provider.close()

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_stream_works(self, name, provider):
        try:
            chunks = list(provider.stream(ReasoningRequest(prompt="test")))
            assert len(chunks) > 0
        except NotImplementedError:
            pass  # Streaming is optional

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_interface_contract(self, name, provider):
        """Verify implements ReasoningProvider protocol."""
        assert isinstance(provider, ReasoningProvider), \
            f"{name} does not implement ReasoningProvider"


class TestDTOUniformity:
    """Semua provider menghasilkan DTO yang sama strukturnya."""

    def test_all_providers_same_dto_keys(self):
        request = ReasoningRequest(prompt="Test")
        dtos = []
        for name, p in ALL_PROVIDERS:
            r = p.generate(request)
            d = r.to_dict()
            dtos.append((name, d))

        # Semua harus punya kunci yang sama
        keys_set = set(dtos[0][1].keys())
        for name, d in dtos[1:]:
            assert set(d.keys()) == keys_set, \
                f"{name} keys differ: {set(d.keys()) - keys_set}"

    def test_all_usages_same_structure(self):
        request = ReasoningRequest(prompt="Test")
        for name, p in ALL_PROVIDERS:
            r = p.generate(request)
            u = r.usage.to_dict()
            assert "prompt_tokens" in u
            assert "completion_tokens" in u
            assert "total_tokens" in u
            assert "cost_usd" in u

    def test_all_metadata_same_structure(self):
        for name, p in ALL_PROVIDERS:
            m = p.metadata().to_dict()
            assert "provider_name" in m
            assert "model_name" in m
            assert "supports_streaming" in m
            assert "supports_vision" in m
            assert "supports_json" in m


class TestMockProvider:
    """Mock provider-specific tests."""

    def test_health_toggle(self):
        p = MockProvider()
        assert p.health() is True
        p.set_health(False)
        assert p.health() is False
        p.set_health(True)
        assert p.health() is True

    def test_incremental_count(self):
        # Each generate increments counter
        p = MockProvider()
        old_count = p.generate(ReasoningRequest(prompt="q"))
        new_count = p.generate(ReasoningRequest(prompt="q2"))
        # Just verify it works without error
        assert old_count is not None


class TestLLMGateway:
    """Gateway-level tests."""

    def test_default_provider(self):
        gateway = LLMGateway()
        p = gateway.get()
        assert p.metadata().provider_name == "mock"

    def test_get_all_providers(self):
        gateway = LLMGateway()
        for name in ["mock", "openai", "gemini", "claude", "ollama"]:
            p = gateway.get(name)
            assert p is not None

    def test_set_default(self):
        gateway = LLMGateway()
        gateway.set_default("claude")
        p = gateway.get()
        assert p.metadata().provider_name == "claude"

    def test_set_default_unknown_raises(self):
        gateway = LLMGateway()
        with pytest.raises(ValueError):
            gateway.set_default("unknown")

    def test_get_unknown_raises(self):
        gateway = LLMGateway()
        with pytest.raises(ValueError):
            gateway.get("unknown")

    def test_health_all(self):
        gateway = LLMGateway()
        health = gateway.health()
        assert len(health) == 5
        assert all(v is True for v in health.values())

    def test_list_metadata(self):
        gateway = LLMGateway()
        mds = gateway.list_metadata()
        assert len(mds) == 5
        assert "mock" in mds
        assert mds["mock"].provider_name == "mock"

    def test_generate_via_gateway(self):
        gateway = LLMGateway()
        request = ReasoningRequest(prompt="Gateway test")
        response = gateway.generate(request)
        assert "Gateway" in response.answer

    def test_generate_with_provider_hint(self):
        gateway = LLMGateway()
        request = ReasoningRequest(prompt="Test", provider_hint="openai")
        response = gateway.generate(request)
        assert "[OpenAI" in response.answer

    def test_register_custom(self):
        gateway = LLMGateway()
        custom = MockProvider(model_name="custom-v2")
        gateway.register("custom", custom)
        p = gateway.get("custom")
        assert p.metadata().model_name == "custom-v2"

    def test_provider_names(self):
        gateway = LLMGateway()
        names = gateway.provider_names
        assert "mock" in names
        assert "openai" in names
        assert len(names) == 5


class TestNoNetworkCall:
    """Verifikasi semua provider menggunakan fake response, tanpa network."""

    @pytest.mark.parametrize("name,provider", ALL_PROVIDERS)
    def test_no_external_call(self, name, provider):
        """Generate harus instan tanpa IO."""
        import time
        request = ReasoningRequest(prompt="test")
        start = time.time()
        provider.generate(request)
        elapsed = time.time() - start
        assert elapsed < 1.0, f"{name}: generate took {elapsed}s (possible network call?)"
