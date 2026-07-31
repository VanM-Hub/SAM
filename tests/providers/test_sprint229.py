"""Test Sprint 229 — LLM Common Adapter (Program A).
Adapter generik: semua penyedia LLM memakai interface sama, immutable,
preview external_calls=0, tanpa network call.
"""
import pytest

from sam.providers.llm import (
    LLMRequest,
    LLMRequestBuilder,
    LLMResponse,
    LLMResponseBuilder,
    LLMMessage,
    LLMRole,
    LLMMessageBuilder,
    LLMModel,
    LLMModelCapability,
    LLMCapability,
    LLMCapabilitySet,
    LLMSession,
    LLMSessionState,
    LLMAdapter,
    LLMAdapterResult,
)
from sam.providers.llm.conversation_llm import ConversationLLMBridge
from sam.providers.llm.dashboard_llm import DashboardLLMBridge, LLMCard
from sam.providers.interfaces.provider_error import ProviderException

FROZEN_DTOS = [
    LLMRequest,
    LLMResponse,
    LLMMessage,
    LLMModel,
    LLMModelCapability,
    LLMCapability,
    LLMCapabilitySet,
    LLMSession,
    LLMAdapterResult,
]


class DummyAdapter(LLMAdapter):
    provider_id = "dummy"

    def models(self):
        m = LLMModel(
            model_id="dummy-1", provider_id="dummy",
            capability=LLMModelCapability(supports_tools=True),
        )
        return [m]

    def build_preview_payload(self, request):
        return {
            "provider": self.provider_id,
            "payload": request.as_dict(),
        }

    def parse_response(self, payload, request):
        return LLMResponse(
            response_id="r-" + request.request_id,
            request_id=request.request_id,
            provider_id=self.provider_id,
            model=request.model,
            text="preview ok",
            usage={"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
        )


class TestLLMMessage:
    def test_message_builder(self):
        m = LLMMessageBuilder("halo").as_user().build()
        assert m.role == LLMRole.USER
        assert m.content == "halo"

    def test_message_frozen(self):
        with pytest.raises(Exception):
            LLMMessage(LLMRole.USER, "x").content = "y"  # type: ignore[misc]

    def test_message_as_dict(self):
        m = LLMMessage(LLMRole.SYSTEM, "sistem")
        assert m.as_dict()["role"] == "system"


class TestLLMRequest:
    def test_request_preview_zero_calls(self):
        req = LLMRequest(request_id="q1", provider_id="openai", model="gpt")
        assert req.external_calls == 0
        assert req.mode == "preview"

    def test_request_builder(self):
        req = (
            LLMRequestBuilder("q2", "openai", "gpt-4")
            .with_system("jadi asisten")
            .add_message(LLMMessageBuilder("berapa 2+2").build())
            .with_temperature(0.0)
            .build()
        )
        assert req.prompt_text() == "[system] jadi asisten\n[user] berapa 2+2"
        assert req.temperature == 0.0

    def test_request_frozen(self):
        with pytest.raises(Exception):
            LLMRequest("q", "p", "m").model = "x"  # type: ignore[misc]


class TestLLMResponse:
    def test_response_builder_usage(self):
        resp = (
            LLMResponseBuilder("s1", "q1", "openai", "gpt")
            .with_text("jawaban")
            .with_usage(10, 5)
            .build()
        )
        assert resp.text == "jawaban"
        assert resp.prompt_tokens == 10
        assert resp.completion_tokens == 5
        assert resp.external_calls == 0


class TestLLMModel:
    def test_model_capability_defaults(self):
        cap = LLMModelCapability()
        assert cap.context_window == 8192
        assert cap.supports_tools is False

    def test_model_key(self):
        m = LLMModel(model_id="gpt-4", provider_id="openai")
        assert m.key == "openai:gpt-4"


class TestLLMCapability:
    def test_supports(self):
        cs = LLMCapabilitySet("openai", ("generate", "chat"))
        assert cs.supports("chat")
        assert not cs.supports("embed")


class TestLLMSession:
    def test_transitions(self):
        s = LLMSession("s", "openai", "gpt").open()
        assert s.state == LLMSessionState.OPEN
        assert s.append(LLMMessage(LLMRole.USER, "hai")).message_count == 1
        assert s.complete().state == LLMSessionState.COMPLETED


class TestLLMAdapter:
    def test_preview_no_external_calls(self):
        adapter = DummyAdapter()
        req = LLMRequest(request_id="q", provider_id="dummy", model="dummy-1")
        result = adapter.preview(req)
        assert result.ok is True
        assert result.external_calls == 0
        assert result.preview is True
        assert result.response.text == "preview ok"

    def test_execution_blocked_in_preview_mode(self):
        adapter = DummyAdapter()
        req = LLMRequest(
            request_id="q", provider_id="dummy", model="dummy-1",
            mode="execute", external_calls=1,
        )
        with pytest.raises(ProviderException):
            adapter.preview(req)

    def test_models_list(self):
        adapter = DummyAdapter()
        assert adapter.models()[0].model_id == "dummy-1"


class TestLLMBridge:
    def test_conversation_bridge(self):
        b = ConversationLLMBridge(DummyAdapter())
        assert b.provider_id() == "dummy"
        assert b.list_models() == ["dummy-1"]
        assert b.count_models() == 1

    def test_dashboard_bridge(self):
        b = DashboardLLMBridge(DummyAdapter())
        card = b.card()
        assert card.provider_id == "dummy"
        assert card.model_count == 1
        assert card.verdict == "ready"
        assert b.available() is True


class TestLLMImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
