"""Test Sprint 233 — DeepSeek Provider (Program A)."""
import pytest

from sam.providers.deepseek import (
    DeepSeekAdapter,
    DeepSeekRequest,
    DeepSeekResponse,
    DeepSeekProviderConfig,
)
from sam.providers.llm import (
    LLMRequest,
    LLMMessageBuilder,
)
from sam.providers.interfaces.provider_error import ProviderException

FROZEN_DTOS = [DeepSeekRequest, DeepSeekResponse, DeepSeekProviderConfig]


class TestDeepSeekConfig:
    def test_defaults(self):
        c = DeepSeekProviderConfig()
        assert c.provider_id == "deepseek"
        assert "deepseek-chat" in c.models
        assert c.preview_only is True

    def test_resolve_model(self):
        c = DeepSeekProviderConfig()
        assert c.resolve_model("deepseek-reasoner") == "deepseek-reasoner"
        assert c.resolve_model("x") == "deepseek-chat"


class TestDeepSeekRequest:
    def test_from_llm(self):
        req = LLMRequest(request_id="q", provider_id="deepseek", model="deepseek-chat")
        d = DeepSeekRequest.from_llm(req)
        assert d.provider_id == "deepseek"
        assert d.external_calls == 0

    def test_wire_messages_with_system(self):
        req = DeepSeekRequest(
            request_id="q", model="deepseek-chat", system="instruksi",
            messages=(LLMMessageBuilder("hai").build(),),
        )
        wire = req.wire_messages()
        assert wire[0] == {"role": "system", "content": "instruksi"}
        assert wire[1] == {"role": "user", "content": "hai"}


class TestDeepSeekResponse:
    def test_to_llm(self):
        resp = DeepSeekResponse(
            response_id="s", request_id="q", model="deepseek-chat", text="jawaban",
            usage={"prompt_tokens": 6, "completion_tokens": 2},
        )
        llm = resp.to_llm()
        assert llm.text == "jawaban"
        assert llm.prompt_tokens == 6


class TestDeepSeekAdapter:
    def test_models_list(self):
        a = DeepSeekAdapter()
        assert all(m.provider_id == "deepseek" for m in a.models())
        assert any(m.model_id == "deepseek-chat" for m in a.models())

    def test_preview_no_external_calls(self):
        a = DeepSeekAdapter()
        req = LLMRequest(request_id="q", provider_id="deepseek", model="deepseek-chat")
        result = a.generate(req)
        assert result.ok is True
        assert result.external_calls == 0
        assert result.preview is True

    def test_preview_payload(self):
        a = DeepSeekAdapter()
        req = LLMRequest(request_id="q", provider_id="deepseek", model="deepseek-chat")
        payload = a.build_preview_payload(req)
        assert payload["provider"] == "deepseek"
        assert payload["endpoint"] == "/chat/completions"
        assert payload["_preview"] is True

    def test_parse_choices(self):
        a = DeepSeekAdapter()
        req = LLMRequest(request_id="q", provider_id="deepseek", model="deepseek-chat")
        payload = {
            "model": "deepseek-chat",
            "choices": [{"message": {"content": "hasil"}, "finish_reason": "stop"}],
            "usage": {"prompt_tokens": 2, "completion_tokens": 1, "total_tokens": 3},
        }
        resp = a.parse_response(payload, req)
        assert resp.text == "hasil"
        assert resp.completion_tokens == 1

    def test_execution_blocked(self):
        a = DeepSeekAdapter()
        req = LLMRequest(
            request_id="q", provider_id="deepseek", model="deepseek-chat",
            mode="execute", external_calls=1,
        )
        with pytest.raises(ProviderException):
            a.generate(req)


class TestDeepSeekImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
