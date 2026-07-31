"""Sprint 263 - Secrets Runtime.

Program D - Runtime Services & Deployment.
Semua secret dari environment. Tidak pernah hardcode.
"""
from __future__ import annotations
import os
import pytest

from sam.runtime_service.secrets import SUPPORTED_SECRETS
from sam.runtime_service.secrets.secret_descriptor import SecretDescriptor
from sam.runtime_service.secrets.secret_provider import SecretProvider
from sam.runtime_service.secrets.secret_resolver import SecretResolver
from sam.runtime_service.secrets.secret_validator import SecretValidator
from sam.runtime_service.secrets.secret_runtime import SecretRuntime


ENV = {
    "OPENAI_API_KEY": "sk-openai-123",
    "ANTHROPIC_API_KEY": "sk-ant-456",
    "GEMINI_API_KEY": "gem-789",
    "OPENROUTER_API_KEY": "or-101112",
    "OLLAMA_HOST": "http://localhost:11434",
}


def test_supported_secrets_present():
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
                "DEEPSEEK_API_KEY", "OPENROUTER_API_KEY",
                "OPENCLAW_URL", "OLLAMA_HOST"):
        assert key in SUPPORTED_SECRETS


def test_descriptor_immutable_and_source():
    d = SecretDescriptor(key="OPENAI_API_KEY", required=True)
    assert d.source == "env"
    with pytest.raises(Exception):
        d.key = "x"
    with pytest.raises(ValueError):
        SecretDescriptor(key="K", source="file")


def test_descriptor_no_secret_value():
    # repr tidak boleh membocorkan nilai
    d = SecretDescriptor(key="OPENAI_API_KEY")
    assert "sk-" not in repr(d)
    assert "env" in repr(d)


def test_descriptor_as_dict():
    d = SecretDescriptor(key="K", required=True)
    ad = d.as_dict()
    assert ad["key"] == "K"
    assert ad["source"] == "env"
    assert "description" in ad


def test_provider_get_from_env():
    p = SecretProvider(env=ENV)
    assert p.get("OPENAI_API_KEY") == "sk-openai-123"


def test_provider_missing_returns_none():
    p = SecretProvider(env=ENV)
    assert p.get("DEEPSEEK_API_KEY") is None
    assert p.has("GEMINI_API_KEY") is True
    assert p.has("NOPE") is False


def test_provider_uses_real_os_environ():
    os.environ["SAM_TEST_SECRET_X"] = "real-env-val"
    p = SecretProvider()
    assert p.get("SAM_TEST_SECRET_X") == "real-env-val"
    del os.environ["SAM_TEST_SECRET_X"]


def test_provider_resolve_all():
    p = SecretProvider(env=ENV)
    out = p.resolve_all(["OPENAI_API_KEY", "OLLAMA_HOST", "MISSING"])
    assert "MISSING" not in out
    assert out["OLLAMA_HOST"] == "http://localhost:11434"


def test_provider_required_raises():
    p = SecretProvider(env=ENV)
    assert p.required("OPENAI_API_KEY") == "sk-openai-123"
    with pytest.raises(KeyError):
        p.required("NOT_SET")


def test_resolver():
    r = SecretResolver(SecretProvider(env=ENV))
    assert r.resolve("ANTHROPIC_API_KEY") == "sk-ant-456"
    assert r.resolve("NOPE") is None
    with pytest.raises(KeyError):
        r.resolve_required("NOPE")


def test_resolver_available():
    r = SecretResolver(SecretProvider(env=ENV))
    out = r.available(["GEMINI_API_KEY", "OPENROUTER_API_KEY"])
    assert out["GEMINI_API_KEY"] == "gem-789"


def test_validator_missing_required():
    v = SecretValidator(SecretProvider(env=ENV))
    missing = v.missing([SecretDescriptor(key="OPENAI_API_KEY", required=True),
                         SecretDescriptor(key="DEEPSEEK_API_KEY", required=True)])
    assert missing == ["DEEPSEEK_API_KEY"]


def test_validator_is_satisfied():
    v = SecretValidator(SecretProvider(env=ENV))
    assert v.is_satisfied([SecretDescriptor(key="OPENAI_API_KEY", required=True)])
    assert not v.is_satisfied([SecretDescriptor(key="DEEPSEEK_API_KEY", required=True)])


def test_runtime_get_and_available():
    rt = SecretRuntime(SecretProvider(env=ENV))
    assert rt.get("OPENAI_API_KEY") == "sk-openai-123"
    assert rt.is_available("ANTHROPIC_API_KEY") is True
    assert rt.is_available("DEEPSEEK_API_KEY") is False
    ap = rt.available_providers()
    assert "OPENAI_API_KEY" in ap
    assert "DEEPSEEK_API_KEY" not in ap


def test_runtime_missing_required():
    rt = SecretRuntime(SecretProvider(env=ENV))
    assert rt.missing_required(["DEEPSEEK_API_KEY"]) == ["DEEPSEEK_API_KEY"]
    assert rt.missing_required(["OPENAI_API_KEY"]) == []


def test_runtime_redact():
    rt = SecretRuntime(SecretProvider(env=ENV))
    assert rt.redact(None) == "<unset>"
    assert rt.redact("sk-openai-123") == "sk****23"
    assert rt.redact("ab") == "****"


def test_no_hardcoded_secret_in_source():
    import inspect
    from sam.runtime_service.secrets import secret_provider
    src = inspect.getsource(secret_provider)
    assert "sk-" not in src
    assert "OPENAI_API_KEY" not in src or "os.environ" in src


def test_provider_does_not_know_other_providers():
    # SecretProvider tidak berinteraksi dengan provider lain
    import inspect
    from sam.runtime_service.secrets import secret_provider
    src = inspect.getsource(secret_provider)
    assert "providers" not in src
