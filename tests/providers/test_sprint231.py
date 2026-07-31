"""Test Sprint 231 — Anthropic Provider (Program A)."""
import pytest

from sam.providers.anthropic import (
    AnthropicAdapter,
    AnthropicRequest,
    AnthropicResponse,
    AnthropicProviderConfig,
)
from sam.providers.llm import (
    LLMRequest,
    LLMMessageBuilder,
)
from sam.providers.interfaces.provider_error import ProviderException

FROZEN_DTOS = [AnthropicRequest, AnthropicResponse, AnthropicProviderConfig]


class TestAnthropicConfig:
    def test_defaults(self):
        c = AnthropicProviderConfig()
        assert c.provider_id == "anthropic"
        assert "claude-sonnet-4-6" in c.models
        assert c.preview_only is True

    def test_resolve_model(self):
        c = AnthropicProviderConfig()
        assert c.resolve_model("claude-opus-4-6") == "claude-opus-4-6"
        assert c.resolve_model("x") == "claude-sonnet-4-6"


class TestAnthropicRequest:
    def test_from_llm(self):
        req = LLMRequest(request_id="q", provider_id="anthropic", model="claude-sonnet-4-6")
        a = AnthropicRequest.from_llm(req)
        assert a.provider_id == "anthropic"
        assert a.external_calls == 0

    def test_wire_messages_tool_maps_to_user(self):
        from sam.providers.llm import LLMRole, LLMMessage
        req = AnthropicRequest(
            request_id="q", model="claude-sonnet-4-6",
            messages=(LLMMessage(LLMRole.TOOL, "hasil tool"),),
        )
        assert req.wire_messages()[0] == {"role": "user", "content": "hasil tool"}


class TestAnthropicResponse:
    def test_to_llm(self):
        from sam.providers.llm import LLMResponse
        resp = AnthropicResponse(
            response_id="s", request_id="q", model="claude-sonnet-4-6",
            text="jawaban", usage={"input_tokens": 5, "output_tokens": 3},
        )
        llm = resp.to_llm()
        assert isinstance(llm, LLMResponse)
        assert llm.text == "jawaban"
        assert llm.prompt_tokens == 5


class TestAnthropicAdapter:
    def test_models_list(self):
        a = AnthropicAdapter()
        assert all(m.provider_id == "anthropic" for m in a.models())
        assert any(m.model_id == "claude-sonnet-4-6" for m in a.models())

    def test_preview_no_external_calls(self):
        a = AnthropicAdapter()
        req = LLMRequest(request_id="q", provider_id="anthropic", model="claude-sonnet-4-6")
        result = a.generate(req)
        assert result.ok is True
        assert result.external_calls == 0
        assert result.preview is True

    def test_preview_payload(self):
        a = AnthropicAdapter()
        req = LLMRequest(
            request_id="q", provider_id="anthropic", model="claude-sonnet-4-6",
            messages=(LLMMessageBuilder("halo").build(),),
        )
        payload = a.build_preview_payload(req)
        assert payload["provider"] == "anthropic"
        assert payload["endpoint"] == "/messages"
        assert payload["_preview"] is True

    def test_parse_anthropic_content_blocks(self):
        a = AnthropicAdapter()
        req = LLMRequest(request_id="q", provider_id="anthropic", model="claude-sonnet-4-6")
        payload = {
            "model": "claude-sonnet-4-6",
            "content": [
                {"type": "text", "text": "bagian satu "},
                {"type": "text", "text": "bagian dua"},
            ],
            "stop_reason": "end_turn",
            "usage": {"input_tokens": 4, "output_tokens": 2},
        }
        resp = a.parse_response(payload, req)
        assert resp.text == "bagian satu bagian dua"
        assert resp.prompt_tokens == 4

    def test_execution_blocked(self):
        a = AnthropicAdapter()
        req = LLMRequest(
            request_id="q", provider_id="anthropic", model="claude-sonnet-4-6",
            mode="execute", external_calls=1,
        )
        with pytest.raises(ProviderException):
            a.generate(req)


class TestAnthropicImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
