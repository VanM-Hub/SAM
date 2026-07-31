"""Test Sprint 228 — Provider Interface (Program A).
Semua provider melalui interface yang sama, immutable, preview external_calls=0.
"""
import pytest

from sam.providers.interfaces import (
    ProviderRequest,
    ProviderRequestBuilder,
    ProviderResponse,
    ProviderResponseBuilder,
    ProviderError,
    ProviderErrorKind,
    ProviderException,
    ProviderCapability,
    ProviderCapabilitySet,
    PROVIDER_CAPABILITY_KEYS,
    ProviderSession,
    ProviderSessionState,
    ProviderFactory,
    ProviderFactoryEntry,
    ProviderRegistry,
    ProviderRegistryEntry,
)

FROZEN_DTOS = [
    ProviderRequest,
    ProviderResponse,
    ProviderError,
    ProviderCapability,
    ProviderCapabilitySet,
    ProviderSession,
    ProviderFactoryEntry,
    ProviderRegistryEntry,
]


class TestProviderRequest:
    def test_request_immutable(self):
        with pytest.raises(Exception):
            ProviderRequest(
                request_id="r1", provider_id="openai", operation="generate"
            ).operation = "chat"  # type: ignore[misc]

    def test_request_default_external_calls_zero(self):
        req = ProviderRequest(
            request_id="r1", provider_id="openai", operation="generate"
        )
        assert req.external_calls == 0
        assert req.mode == "preview"

    def test_request_builder_preview(self):
        req = (
            ProviderRequestBuilder("r2", "openai", "chat")
            .with_payload({"prompt": "halo"})
            .with_parameter("temperature", 0.2)
            .build()
        )
        assert req.payload["prompt"] == "halo"
        assert req.parameters["temperature"] == 0.2
        assert req.external_calls == 0

    def test_request_as_dict(self):
        req = ProviderRequest(
            request_id="r3", provider_id="gemini", operation="embed"
        )
        d = req.as_dict()
        assert d["provider_id"] == "gemini"
        assert d["external_calls"] == 0


class TestProviderResponse:
    def test_response_success(self):
        resp = (
            ProviderResponseBuilder("s1", "r1", "openai", "generate")
            .with_data({"text": "jawaban"})
            .build()
        )
        assert resp.ok is True
        assert resp.data["text"] == "jawaban"
        assert resp.external_calls == 0

    def test_response_failure(self):
        resp = (
            ProviderResponseBuilder("s2", "r1", "openai", "generate")
            .failed("rate_limited", "terlalu banyak")
            .build()
        )
        assert resp.ok is False
        assert resp.error_code == "rate_limited"
        assert resp.external_calls == 0


class TestProviderError:
    def test_error_kind_preview_only(self):
        err = ProviderError(
            code="PREVIEW",
            kind=ProviderErrorKind.PREVIEW_ONLY,
            message="preview tidak boleh execute",
            provider_id="openai",
        )
        assert err.kind.value == "preview_only"
        assert err.retryable is False

    def test_provider_exception_carries_error(self):
        err = ProviderError(
            code="NS", kind=ProviderErrorKind.NOT_SUPPORTED, message="tidak support"
        )
        exc = ProviderException(err)
        assert exc.error.code == "NS"
        assert str(exc) == "[not_supported] tidak support"


class TestProviderCapability:
    def test_capability_keys(self):
        assert "generate" in PROVIDER_CAPABILITY_KEYS
        assert "tool_call" in PROVIDER_CAPABILITY_KEYS

    def test_capability_default_preview(self):
        cap = ProviderCapability("openai", "generate")
        assert cap.supported is True
        assert cap.mode == "preview"
        assert cap.external_calls == 0

    def test_capability_set_supports(self):
        cset = ProviderCapabilitySet("openai", ("generate", "chat"))
        assert cset.supports("generate") is True
        assert cset.supports("embed") is False
        assert cset.count == 2


class TestProviderSession:
    def test_session_transitions(self):
        s = ProviderSession("sess1", "openai").open()
        assert s.is_open
        closed = s.close()
        assert closed.state == ProviderSessionState.CLOSED
        assert closed.history == ("close",)

    def test_session_immutable(self):
        s = ProviderSession("sess1", "openai")
        with pytest.raises(Exception):
            s.state = ProviderSessionState.OPEN  # type: ignore[misc]


class TestProviderFactory:
    def test_factory_register_create(self):
        factory = ProviderFactory()
        ok = factory.register("openai", lambda: "OpenAIInstance", adapter_type="llm")
        assert ok
        assert factory.has("openai")
        assert factory.create("openai") == "OpenAIInstance"
        assert factory.count() == 1

    def test_factory_no_duplicate(self):
        factory = ProviderFactory()
        factory.register("x", lambda: 1)
        assert factory.register("x", lambda: 2) is False

    def test_factory_unknown_raises(self):
        factory = ProviderFactory()
        with pytest.raises(KeyError):
            factory.create("nope")

    def test_factory_entry(self):
        factory = ProviderFactory()
        factory.register("gemini", lambda: None, adapter_type="llm", version="2.0.0")
        e = factory.entry("gemini")
        assert e is not None and e.adapter_type == "llm"
        assert e.version == "2.0.0"


class TestProviderRegistry:
    def test_registry_register_get(self):
        reg = ProviderRegistry()
        entry = ProviderRegistryEntry("openai", "OpenAI", kind="llm")
        assert reg.register(entry) is True
        assert reg.get("openai").name == "OpenAI"

    def test_registry_enabled_and_kind(self):
        reg = ProviderRegistry()
        reg.register(ProviderRegistryEntry("a", "A", kind="llm"))
        reg.register(ProviderRegistryEntry("b", "B", kind="local", enabled=False))
        reg.register(ProviderRegistryEntry("c", "C", kind="local"))
        assert reg.count() == 3
        assert reg.enabled_ids() == ["a", "c"]
        assert reg.by_kind("llm") == ["a"]

    def test_registry_no_duplicate(self):
        reg = ProviderRegistry()
        reg.register(ProviderRegistryEntry("a", "A"))
        assert reg.register(ProviderRegistryEntry("a", "A2")) is False

    def test_registry_entries_ordered(self):
        reg = ProviderRegistry()
        reg.register(ProviderRegistryEntry("b", "B"))
        reg.register(ProviderRegistryEntry("a", "A"))
        names = [e.provider_id for e in reg.entries()]
        assert names == ["a", "b"]


class TestInterfacesImmutability:
    @pytest.mark.parametrize("cls", FROZEN_DTOS)
    def test_dto_frozen(self, cls):
        assert cls.__dataclass_params__.frozen is True
