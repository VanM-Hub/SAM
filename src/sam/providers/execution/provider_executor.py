"""Provider Executor - eksekusi nyata provider (Sprint 260).

Program C - Real Execution Runtime.
KONTAK: memanggil provider nyata HANYA saat execute + approval valid.
Provider-specific code berada DI SINI (provider layer), bukan di runtime.

Program K K2 - Provider Runtime Activation:
- MengOPERASIONALKAN ProviderExecutor yang sebelumnya stub: `execute()` kini
  melakukan panggilan HTTP NYATA ke provider LLM via `httpx`.
- Dihubungkan ke adapter provider yang SUDAH ADA (LLMAdapter di providers/<vendor>)
  lewat injection DI dari composition root (intra provider layer; TIDAK ada
  dependency antar-layer baru).
- Mekanisme dipilih Engineering: `httpx` (sudah menjadi dependency pyproject;
  TIDAK menambah SDK provider baru -> tidak mengubah arsitektur).
- Network HANYA terjadi di `execute()`, yang sudah di-gate ke mode `execute`
  + approval oleh `ProviderActivationExecutor`. Preview selalu external_calls == 0.

Aturan:
- API key dibaca dari environment/config, TIDAK di-hardcode.
- Jika provider tidak punya kredensial / tidak ada di config -> unavailable.
"""
from __future__ import annotations
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import httpx

from ..llm.llm_request import LLMRequest
from ..llm.llm_message import LLMMessage, LLMRole
from ..llm.llm_adapter import LLMAdapter

# Nama env var per provider (tidak berisi nilai kredensial).
# Nilai dibaca saat execute, dari environment/config.
PROVIDER_ENV = {
    "openai": ("OPENAI_API_KEY", "https://api.openai.com/v1"),
    "anthropic": ("ANTHROPIC_API_KEY", "https://api.anthropic.com"),
    "gemini": ("GEMINI_API_KEY", "https://generativelanguage.googleapis.com"),
    "deepseek": ("DEEPSEEK_API_KEY", "https://api.deepseek.com"),
    "ollama": ("OLLAMA_HOST", "http://localhost:11434"),
    "filesystem": ("", ""),
    "shell": ("", ""),
    "sqlite": ("", ""),
    "docker": ("DOCKER_HOST", ""),
    "openclaw": ("OPENCLAW_GATEWAY", "http://127.0.0.1:18789"),
}


@dataclass(frozen=True)
class ProviderExecutionConfig:
    """Konfigurasi eksekusi provider (immutable)."""
    provider_id: str
    base_url: str = ""
    api_key_env: str = ""

    def has_credentials(self) -> bool:
        if not self.api_key_env:
            return True  # provider non-auth (filesystem, shell, dll)
        return bool(os.environ.get(self.api_key_env, ""))


class ProviderUnavailableError(Exception):
    """Provider tidak tersedia / tanpa kredensial."""


class ProviderExecutor:
    """Executor generik ke provider.

    TIDAK berisi logic khusus satu provider (dari sisi delegasi) --- memilih
    konfigurasi berdasar provider_id dan men-delegasikan panggilan ke
    implementasi di lapisan ini. Network hanya pada execute.

    Program K K2: menerima peta `adapters` (LLMAdapter yang SUDAH ADA) lewat
    DI. Bila adapter tersedia untuk provider, wire-format & parsing memakai
    adapter tsb; bila tidak, dipakai payload generik. Eksekusi nyata selalu
    lewat HTTP (httpx) ke `base_url` provider.
    """

    def __init__(self, configs: Dict[str, ProviderExecutionConfig] | None = None,
                 adapters: Dict[str, LLMAdapter] | None = None) -> None:
        self._configs = configs or {
            pid: ProviderExecutionConfig(provider_id=pid, base_url=url,
                                         api_key_env=env)
            for pid, (env, url) in PROVIDER_ENV.items()
        }
        self._adapters: Dict[str, LLMAdapter] = dict(adapters or {})

    def register_adapter(self, provider_id: str, adapter: LLMAdapter) -> None:
        """Daftarkan adapter LLM untuk provider (intra provider layer)."""
        self._adapters[provider_id] = adapter

    def config(self, provider_id: str) -> ProviderExecutionConfig:
        if provider_id not in self._configs:
            raise ProviderUnavailableError(f"provider tidak dikenal: {provider_id}")
        return self._configs[provider_id]

    def available(self, provider_id: str) -> bool:
        try:
            return self.config(provider_id).has_credentials()
        except ProviderUnavailableError:
            return False

    def _api_key(self, cfg: ProviderExecutionConfig) -> str:
        if not cfg.api_key_env:
            return ""
        return os.environ.get(cfg.api_key_env, "")

    def _build_request(self, provider_id: str, operation: str,
                       payload: Dict[str, Any]) -> LLMRequest:
        """Bangun LLMRequest generik dari payload eksekusi (deterministik)."""
        messages = payload.get("messages", [] if payload.get("prompt") is None else [
            {"role": "user", "content": str(payload.get("prompt"))},
        ])
        llm_messages = tuple(
            LLMMessage(
                role=LLMRole(m.get("role", "user")) if m.get("role") in
                ("user", "assistant", "system") else LLMRole("user"),
                content=str(m.get("content", "")),
            )
            for m in messages
            if isinstance(m, dict) and m.get("content")
        )
        return LLMRequest(
            request_id=str(payload.get("execution_id", "exec-" + provider_id)),
            provider_id=provider_id,
            model=str(payload.get("model", "default")),
            messages=llm_messages,
            temperature=float(payload.get("temperature", 0.2)),
            max_tokens=int(payload.get("max_tokens", 1024)),
            system=str(payload.get("system", "")) or None,
            mode="execute",
            metadata=dict(payload),
        )

    def _endpoint(self, operation: str) -> str:
        """Endpoint HTTP untuk operasi provider (default chat completions)."""
        if operation in ("chat", "complete", "completions"):
            return "/chat/completions"
        if operation == "models":
            return "/models"
        return f"/{operation.lstrip('/')}"

    def _call_http(self, cfg: ProviderExecutionConfig, url: str,
                   body: Dict[str, Any], api_key: str,
                   timeout_seconds: int) -> Dict[str, Any]:
        """Panggilan HTTP nyata via httpx (hanya di execute, sudah di-gate)."""
        headers = {"Content-Type": "application/json"}
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        resp = httpx.post(
            url,
            json=body,
            headers=headers,
            timeout=httpx.Timeout(timeout_seconds),
        )
        resp.raise_for_status()
        data = resp.json()
        if not isinstance(data, dict):
            data = {"result": data}
        return data

    def execute(self, provider_id: str, operation: str,
                payload: Optional[Dict[str, Any]] = None,
                timeout_seconds: int = 60) -> Dict[str, Any]:
        """Eksekusi nyata. Lempar ProviderUnavailableError bila tak ada kredensial.

        caller (Execution Runtime) WAJIB sudah menegaskan approval sebelum
        memanggil ini (mode execute). Di sini dilakukan panggilan HTTP nyata
        ke provider LLM via httpx, dihubungkan ke adapter yang SUDAH ADA
        (bila terdaftar) untuk wire-format & parsing.
        """
        cfg = self.config(provider_id)
        if not cfg.has_credentials():
            raise ProviderUnavailableError(
                f"provider '{provider_id}' tanpa kredensial (env {cfg.api_key_env or 'n/a'})")
        if not cfg.base_url:
            raise ProviderUnavailableError(
                f"provider '{provider_id}' tanpa base_url untuk eksekusi LLM")

        payload = dict(payload or {})
        api_key = self._api_key(cfg)
        adapter = self._adapters.get(provider_id)
        request = self._build_request(provider_id, operation, payload)

        if adapter is not None:
            # Wire-format via adapter yang SUDAH ADA (intra layer).
            wire = adapter.build_preview_payload(request)
        else:
            wire = {
                "model": request.model,
                "messages": [m.as_dict() for m in request.messages],
                "temperature": request.temperature,
                "max_tokens": request.max_tokens,
            }

        url = cfg.base_url.rstrip("/") + self._endpoint(operation)
        raw = self._call_http(cfg, url, wire, api_key, timeout_seconds)

        if adapter is not None:
            response = adapter.parse_response(raw, request)
            parsed_payload = response.as_dict()
        else:
            parsed_payload = {
                "provider_id": provider_id,
                "operation": operation,
                "raw": raw,
            }

        return {
            "provider_id": provider_id,
            "operation": operation,
            "status": "completed",
            "payload": parsed_payload,
            "external_calls": 1,
        }
