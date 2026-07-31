"""Test Sprint 234 — Ollama Provider (Program A, model lokal)."""
import pytest

from sam.providers.ollama import (
    OllamaAdapter,
    OllamaRequest,
    OllamaResponse,
    OllamaProviderConfig,
)
from sam.providers.llm import (
    LLMRequest,
    LLMMessageBuilder,
)
from sam.providers.interfaces.provider_error import ProviderException

FROZEN_DTOS = [OllamaRequest, OllamaResponse, OllamaProviderConfig]


class TestOllamaConfig:
    def test_defaults(self):
        c = OllamaProviderConfig()
        assert c.provider_id == "ollama"
        assert "llama3.3-70b" in c.models
        assert c.preview_only is True

    def test_resolve_model(self):
        c = OllamaProviderConfig()
        assert c.resolve_model("llama3.2") == "llama3.2"
        assert c.resolve_model("x") == "llama3.3-70b"


class TestOllamaRequest:
    def test_from_llm(self):
        req = LLMRequest(request_id="q", provider_id="ollama", model="llama3.3-70b")
        o = OllamaRequest.from_llm(req)
        assert o.provider_id == "ollama"
        assert o.external_calls == 0
        assert o.num_predict == 1024

    def test_prompt_text_with_system(self):
        req = OllamaRequest(
            request_id="q", model="llama3.3-70b", system="instruksi",
            messages=(LLMMessageBuilder("hai").build(),),
        )
        assert req.prompt_text() == "System: instruksi\nhai"


class TestOllamaResponse:
    def test_to_llm(self):
        resp = OllamaResponse(
            response_id="s", request_id="q", model="llama3.3-70b",
            text="jawaban", eval_count=3, prompt_eval_count=5,
        )
        llm = resp.to_llm()
        assert llm.text == "jawaban"
        assert llm.prompt_tokens == 5
        assert llm.completion_tokens == 3


class TestOllamaAdapter:
    def test_models_list(self):
        a = OllamaAdapter()
        assert all(m.provider_id == "ollama" for m in a.models())
        assert any(m.model_id == "llama3.3-70b" for m in a.models())

    def test_preview_no_external_calls(self):
        a = OllamaAdapter()
        req = LLMRequest(request_id="q", provider_id="ollama", model="llama3.3-70b")
        result = a.generate(req)
        assert result.ok is True
        assert result.external_calls == 0
        assert result.preview is True

    def test_preview_payload(self):
        a = OllamaAdapter()
        req = LLMRequest(request_id="q", provider_id="ollama", model="llama3.3-70b")
        payload = a.build_preview_payload(req)
        assert payload["provider"] == "ollama"
        assert payload["endpoint"] == "/api/generate"
        assert payload["stream"] is False

    def test_parse_response(self):
        a = OllamaAdapter()
        req = LLMRequest(request_id="q", provider_id="ollama", model="llama3.3-70b")
        payload = {"model": "llama3.3-70b", "response": "hasil", "done": True,
                   "eval_count": 2, "prompt_eval_count": 4}
        resp = a.parse_response(payload, req)
        assert resp.text == "hasil"
        assert resp.completion_tokens == 2

    def test_execution_blocked(self):
        a = OllamaAdapter()
        req = LLMRequest(
            request_id="q", provider_id="ollama", model="llama3.3-70b",
            mode="execute", external_calls=1,
        )
        with pytest.raises(ProviderException):
            a.generate(req)


class TestOllamaImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
