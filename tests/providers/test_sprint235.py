"""Test Sprint 235 — OpenClaw Runtime Integration (Program A)."""
import pytest

from sam.providers.integration.runtime_integration import (
    ProviderIntegration,
    ProviderIntegrationResult,
    ProviderRuntimeManifest,
)
from sam.providers.integration.openclaw_gateway import (
    OpenClawGateway,
    OpenClawGatewayToolRequest,
)
from sam.providers.llm import LLMRequest, LLMMessageBuilder
from sam.providers.openai import OpenAIAdapter
from sam.providers.anthropic import AnthropicAdapter
from sam.providers.gemini import GeminiAdapter
from sam.providers.deepseek import DeepSeekAdapter
from sam.providers.ollama import OllamaAdapter

FROZEN_DTOS = [
    ProviderIntegrationResult,
    ProviderRuntimeManifest,
    OpenClawGatewayToolRequest,
]


def build_integration():
    it = ProviderIntegration()
    it.register(OpenAIAdapter())
    it.register(AnthropicAdapter())
    it.register(GeminiAdapter())
    it.register(DeepSeekAdapter())
    it.register(OllamaAdapter())
    return it


class TestProviderIntegration:
    def test_register_all_providers(self):
        it = build_integration()
        assert it.count() == 5
        assert set(it.list_providers()) == {
            "openai", "anthropic", "gemini", "deepseek", "ollama"
        }

    def test_no_duplicate(self):
        it = ProviderIntegration()
        assert it.register(OpenAIAdapter()) is True
        assert it.register(OpenAIAdapter()) is False

    def test_unregister(self):
        it = build_integration()
        assert it.unregister("ollama") is True
        assert it.count() == 4
        assert it.unregister("ollama") is False

    def test_generate_preview_external_zero(self):
        it = build_integration()
        req = LLMRequest(request_id="q", provider_id="openai", model="gpt-4o-mini")
        res = it.generate(req)
        assert res.ok is True
        assert res.external_calls == 0
        assert res.preview is True

    def test_generate_unknown_provider(self):
        it = build_integration()
        req = LLMRequest(request_id="q", provider_id="nope", model="x")
        res = it.generate(req)
        assert res.ok is False
        assert "unknown provider" in res.detail

    def test_models_per_provider(self):
        it = build_integration()
        assert len(it.models("openai")) > 0
        assert it.models("gemini")[0].provider_id == "gemini"

    def test_manifest(self):
        it = build_integration()
        m = it.manifest()
        assert m.provider_ids == ("anthropic", "deepseek", "gemini", "ollama", "openai")
        assert m.external_calls == 0


class TestOpenClawGateway:
    def test_request_tool_preview_not_invoked(self):
        g = OpenClawGateway(build_integration())
        req = g.request_tool("read_file", {"path": "x.txt"})
        assert req.preview is True
        assert req.invoked is False
        assert req.external_calls == 0

    def test_gateway_providers(self):
        g = OpenClawGateway(build_integration())
        assert g.count_providers() == 5
        assert g.is_ready() is True
        assert "openai" in g.available_providers()

    def test_gateway_empty_not_ready(self):
        g = OpenClawGateway()
        assert g.is_ready() is False


class TestIntegrationImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
