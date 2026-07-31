"""Test Sprint 232 — Gemini Provider (Program A)."""
import pytest

from sam.providers.gemini import (
    GeminiAdapter,
    GeminiRequest,
    GeminiResponse,
    GeminiProviderConfig,
)
from sam.providers.llm import (
    LLMRequest,
    LLMMessageBuilder,
)
from sam.providers.interfaces.provider_error import ProviderException

FROZEN_DTOS = [GeminiRequest, GeminiResponse, GeminiProviderConfig]


class TestGeminiConfig:
    def test_defaults(self):
        c = GeminiProviderConfig()
        assert c.provider_id == "gemini"
        assert "gemini-2.5-flash" in c.models
        assert c.preview_only is True

    def test_resolve_model(self):
        c = GeminiProviderConfig()
        assert c.resolve_model("gemini-2.5-pro") == "gemini-2.5-pro"
        assert c.resolve_model("x") == "gemini-2.5-flash"


class TestGeminiRequest:
    def test_from_llm(self):
        req = LLMRequest(request_id="q", provider_id="gemini", model="gemini-2.5-flash")
        g = GeminiRequest.from_llm(req)
        assert g.provider_id == "gemini"
        assert g.external_calls == 0
        assert g.max_output_tokens == 1024

    def test_wire_parts_with_system(self):
        req = GeminiRequest(
            request_id="q", model="gemini-2.5-flash", system="instruksi",
            messages=(LLMMessageBuilder("hai").build(),),
        )
        parts = req.wire_parts()
        assert parts[0] == {"text": "instruksi"}
        assert parts[1] == {"text": "hai"}


class TestGeminiResponse:
    def test_to_llm_normalizes_usage(self):
        resp = GeminiResponse(
            response_id="s", request_id="q", model="gemini-2.5-flash",
            text="jawaban", usage={"promptTokenCount": 7, "candidatesTokenCount": 4},
        )
        llm = resp.to_llm()
        assert llm.text == "jawaban"
        assert llm.prompt_tokens == 7
        assert llm.completion_tokens == 4


class TestGeminiAdapter:
    def test_models_list(self):
        a = GeminiAdapter()
        assert all(m.provider_id == "gemini" for m in a.models())
        assert any(m.model_id == "gemini-2.5-pro" for m in a.models())

    def test_preview_no_external_calls(self):
        a = GeminiAdapter()
        req = LLMRequest(request_id="q", provider_id="gemini", model="gemini-2.5-flash")
        result = a.generate(req)
        assert result.ok is True
        assert result.external_calls == 0
        assert result.preview is True

    def test_preview_payload(self):
        a = GeminiAdapter()
        req = LLMRequest(request_id="q", provider_id="gemini", model="gemini-2.5-flash")
        payload = a.build_preview_payload(req)
        assert payload["provider"] == "gemini"
        assert ":generateContent" in payload["endpoint"]
        assert payload["_preview"] is True

    def test_parse_gemini_candidates(self):
        a = GeminiAdapter()
        req = LLMRequest(request_id="q", provider_id="gemini", model="gemini-2.5-flash")
        payload = {
            "model": "gemini-2.5-flash",
            "candidates": [
                {
                    "content": {"parts": [{"text": "hasil A"}, {"text": " hasil B"}]},
                    "finishReason": "STOP",
                }
            ],
            "usageMetadata": {"promptTokenCount": 3, "candidatesTokenCount": 2},
        }
        resp = a.parse_response(payload, req)
        assert resp.text == "hasil A hasil B"
        assert resp.prompt_tokens == 3

    def test_execution_blocked(self):
        a = GeminiAdapter()
        req = LLMRequest(
            request_id="q", provider_id="gemini", model="gemini-2.5-flash",
            mode="execute", external_calls=1,
        )
        with pytest.raises(ProviderException):
            a.generate(req)


class TestGeminiImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
