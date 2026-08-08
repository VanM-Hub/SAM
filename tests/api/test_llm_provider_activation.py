"""K2 - Provider Runtime Activation (unit tests, no real network).

Membuktikan ProviderExecutor yang sebelumnya STUB kini diOPERASIONALKAN:
- Terhubung ke adapter provider yang SUDAH ADA (LLMAdapter di providers/<vendor>).
- `available()` tetap gate kredensial (tanpa kredensial => unavailable, no call).
- Wire-format memakai adapter `build_preview_payload` pada jalur execute.
- Eksekusi HTTP nyata via httpx dibuktikan dengan MockTransport (integration-path,
  tanpa kredensial asli); external_calls=1 pada execute sukses.
- Registry provider terdaftar dengan `implements=<connector contract>` (link
  resmi Connector -> Provider, urutan dipertahankan).
"""
import os

import pytest

from sam.api.llm_wiring import (
    LLM_CONNECTOR_CONTRACT_ID,
    llm_provider_layer,
    provider_activation,
)
from sam.providers.execution.provider_executor import (
    ProviderExecutor,
    ProviderUnavailableError,
)


class TestProviderRegistry:
    """Provider baseline terdaftar dengan link Connector -> Provider."""

    def test_provider_adapter_yang_ada_terdaftar(self) -> None:
        registry = llm_provider_layer.registry
        ids = registry.list_ids()
        # Adapter yang SUDAH ADA di repository, bukan konsep baru.
        assert {"openai", "anthropic", "gemini", "deepseek", "ollama"} == set(ids)

    def test_semua_provider_implements_connector_contract(self) -> None:
        registry = llm_provider_layer.registry
        for pid in registry.list_ids():
            desc = registry.get(pid)
            assert desc is not None
            assert LLM_CONNECTOR_CONTRACT_ID in desc.implements

    def test_activation_report(self) -> None:
        report = provider_activation()
        assert report["contract"] == LLM_CONNECTOR_CONTRACT_ID
        assert len(report["providers"]) == 5


class TestProviderExecutorOperational:
    """ProviderExecutor terprogramkan & terhubung ke adapter."""

    def test_executor_memiliki_adapter_terdaftar(self) -> None:
        # Semua adapter LLM yang ada diregistrasi ke executor (intra layer).
        executor = llm_provider_layer.executor
        for pid in ("openai", "anthropic", "gemini", "deepseek", "ollama"):
            assert pid in executor._adapters

    def test_available_gate_kredensial(self) -> None:
        # Tanpa kredensial env, provider unavailable -> no call (safe).
        self._clear_env()
        for pid in ("openai", "anthropic", "gemini", "deepseek"):
            assert llm_provider_layer.available(pid) is False

    def test_execute_tanpa_kredensial_lempar_unavailable(self) -> None:
        self._clear_env()
        with pytest.raises(ProviderUnavailableError):
            llm_provider_layer.executor.execute("openai", "chat", payload={"prompt": "hi"})

    def test_execute_ok_dengan_httpx_mock(self) -> None:
        """Integration-path: execute nyata via httpx, transport dimock.

        Membuktikan ProviderExecutor benar-benar memanggil HTTP LLM (bukan stub),
        dengan external_calls=1 dan parsing memakai adapter (OpenAI).
        """
        import json

        import httpx

        self._set_env("OPENAI_API_KEY", "sk-test")

        def handler(request: httpx.Request) -> httpx.Response:
            body = json.loads(request.content)
            # wire-format harus dari adapter (endpoint chat/completions, model).
            assert request.url.path.endswith("/chat/completions")
            return httpx.Response(
                200, json={
                    "id": "r1", "model": body.get("model", "gpt-4o"),
                    "choices": [{"message": {"role": "assistant", "content": "ok"},
                                 "finish_reason": "stop"}],
                    "usage": {"prompt_tokens": 5, "completion_tokens": 3, "total_tokens": 8},
                },
            )

        transport = httpx.MockTransport(handler)
        executor = ProviderExecutor()
        executor.register_adapter("openai", __import__(
            "sam.providers.openai.openai_provider", fromlist=["OpenAIAdapter"]
        ).OpenAIAdapter())
        executor._configs["openai"] = executor._configs["openai"].__class__(
            provider_id="openai",
            base_url="https://api.openai.com/v1",
            api_key_env="OPENAI_API_KEY",
        )

        # Monkeypatch `httpx.post` pada module `httpx` (bukan atribut modul
        # ProviderExecutor — httpx di-import lazy di _call_http). Membuktikan
        # jalur HTTP nyata tanpa kredensial asli.
        import httpx
        from unittest import mock

        original_post = httpx.post

        def fake_post(url: str, json=None, headers=None, timeout=None):
            req = httpx.Request("POST", url, json=json or {}, headers=headers or {})
            resp = transport.handle_request(req)
            resp.request = req  # agar raise_for_status() valid
            return resp

        with mock.patch("httpx.post", fake_post):
            result = executor.execute(
                "openai", "chat",
                payload={"prompt": "hello", "model": "gpt-4o"},
            )

        assert result["status"] == "completed"
        assert result["external_calls"] == 1
        assert result["payload"]["provider_id"] == "openai"

        self._clear_env()

    @staticmethod
    def _set_env(key: str, value: str) -> None:
        os.environ[key] = value

    @staticmethod
    def _clear_env() -> None:
        for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
                    "DEEPSEEK_API_KEY"):
            os.environ.pop(key, None)
