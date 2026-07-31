"""Test Sprint 230 — OpenAI Provider (Program A).
Adapter OpenAI mengimplement LLMAdapter: preview-only, external_calls=0,
tanpa network call, semua via interface yang sama.
"""
import pytest

from sam.providers.openai import (
    OpenAIAdapter,
    OpenAIRequest,
    OpenAIResponse,
    OpenAIProviderConfig,
)
from sam.providers.llm import (
    LLMRequest,
    LLMRequestBuilder,
    LLMMessageBuilder,
)
from sam.providers.interfaces.provider_error import ProviderException

FROZEN_DTOS = [OpenAIRequest, OpenAIResponse, OpenAIProviderConfig]


class TestOpenAIConfig:
    def test_default_models(self):
        c = OpenAIProviderConfig()
        assert c.provider_id == "openai"
        assert "gpt-4o-mini" in c.models
        assert c.preview_only is True

    def test_supports_and_resolve(self):
        c = OpenAIProviderConfig()
        assert c.supports_model("gpt-4o")
        assert c.resolve_model("gpt-4o") == "gpt-4o"
        assert c.resolve_model("unknown-model") == "gpt-4o-mini"


class TestOpenAIRequest:
    def test_from_llm(self):
        req = LLMRequest(request_id="q1", provider_id="openai", model="gpt-4o-mini")
        oai = OpenAIRequest.from_llm(req)
        assert oai.provider_id == "openai"
        assert oai.external_calls == 0
        assert oai.mode == "preview"

    def test_wire_messages_with_system(self):
        req = OpenAIRequest(
            request_id="q2",
            model="gpt-4o-mini",
            system="kamu asisten",
            messages=(LLMMessageBuilder("hai").build(),),
        )
        wire = req.wire_messages()
        assert wire[0] == {"role": "system", "content": "kamu asisten"}
        assert wire[1] == {"role": "user", "content": "hai"}


class TestOpenAIResponse:
    def test_to_llm(self):
        resp = OpenAIResponse(
            response_id="s1", request_id="q1", model="gpt-4o-mini",
            text="jawaban", usage={"prompt_tokens": 5, "completion_tokens": 3},
        )
        llm = resp.to_llm()
        assert llm.provider_id == "openai"
        assert llm.text == "jawaban"
        assert llm.prompt_tokens == 5


class TestOpenAIAdapter:
    def test_models_list(self):
        a = OpenAIAdapter()
        assert all(m.provider_id == "openai" for m in a.models())
        assert any(m.model_id == "gpt-4o-mini" for m in a.models())

    def test_preview_no_external_calls(self):
        a = OpenAIAdapter()
        req = LLMRequest(request_id="q", provider_id="openai", model="gpt-4o-mini")
        result = a.generate(req)
        assert result.ok is True
        assert result.external_calls == 0
        assert result.preview is True
        assert result.response.text == ""

    def test_preview_payload_deterministic(self):
        a = OpenAIAdapter()
        req = LLMRequest(
            request_id="q", provider_id="openai", model="gpt-4o-mini",
            messages=(LLMMessageBuilder("halo").build(),),
        )
        payload = a.build_preview_payload(req)
        assert payload["provider"] == "openai"
        assert payload["endpoint"] == "/chat/completions"
        assert payload["_preview"] is True
        assert payload["messages"][0]["role"] == "user"

    def test_execution_blocked(self):
        a = OpenAIAdapter()
        req = LLMRequest(
            request_id="q", provider_id="openai", model="gpt-4o-mini",
            mode="execute", external_calls=1,
        )
        with pytest.raises(ProviderException):
            a.generate(req)


class TestOpenAIImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
