"""Provider Integration — runtime terpadu semua adapter LLM (Sprint 235).

Menggabungkan semua LLMAdapter (OpenAI, Anthropic, Gemini, DeepSeek, Ollama)
ke satu runtime yang dipakai Conversation/Dashboard/Agent. Preview-only.
Tidak menyentuh legacy runtime.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

from ..llm.llm_adapter import LLMAdapter, LLMAdapterResult
from ..llm.llm_request import LLMRequest
from ..llm.llm_response import LLMResponse
from ..llm.llm_model import LLMModel
from ..interfaces.provider_registry import (
    ProviderRegistry,
    ProviderRegistryEntry,
)


@dataclass(frozen=True)
class ProviderRuntimeManifest:
    """Manifest runtime provider (immutable)."""
    runtime_id: str
    provider_ids: Tuple[str, ...] = field(default_factory=tuple)
    version: str = "1.0.0"
    preview_only: bool = True
    external_calls: int = 0


@dataclass(frozen=True)
class ProviderIntegrationResult:
    """Hasil satu operasi integrasi (immutable)."""
    provider_id: str
    ok: bool = True
    preview: bool = True
    external_calls: int = 0
    response: Optional[LLMResponse] = None
    detail: str = ""


class ProviderIntegration:
    """Runtime integrasi: daftar adapter, routing, preview konkuren deterministik."""

    def __init__(self) -> None:
        self._adapters: Dict[str, LLMAdapter] = {}
        self._registry = ProviderRegistry()

    def register(self, adapter: LLMAdapter) -> bool:
        pid = adapter.provider_id
        if pid in self._adapters:
            return False
        self._adapters[pid] = adapter
        self._registry.register(
            ProviderRegistryEntry(
                provider_id=pid,
                name=pid,
                kind="llm",
                enabled=True,
                preview_only=True,
                external_calls=0,
            )
        )
        return True

    def unregister(self, provider_id: str) -> bool:
        if provider_id not in self._adapters:
            return False
        del self._adapters[provider_id]
        return True

    def has(self, provider_id: str) -> bool:
        return provider_id in self._adapters

    def list_providers(self) -> List[str]:
        return sorted(self._adapters.keys())

    def count(self) -> int:
        return len(self._adapters)

    def models(self, provider_id: str) -> List[LLMModel]:
        a = self._adapters.get(provider_id)
        return a.models() if a else []

    def describe(self, provider_id: str) -> str:
        a = self._adapters.get(provider_id)
        return a.provider_id if a else "unknown"

    def generate(self, request: LLMRequest) -> ProviderIntegrationResult:
        """Jalankan preview pada provider yang dituju. Preview-only."""
        pid = request.provider_id
        adapter = self._adapters.get(pid)
        if adapter is None:
            return ProviderIntegrationResult(
                provider_id=pid, ok=False, detail=f"unknown provider '{pid}'"
            )
        try:
            result: LLMAdapterResult = adapter.generate(request)
            return ProviderIntegrationResult(
                provider_id=pid,
                ok=result.ok,
                preview=result.preview,
                external_calls=result.external_calls,
                response=result.response,
                detail="ok",
            )
        except Exception as exc:  # pragma: no cover - guard
            return ProviderIntegrationResult(
                provider_id=pid, ok=False, detail=str(exc)
            )

    def manifest(self) -> ProviderRuntimeManifest:
        return ProviderRuntimeManifest(
            runtime_id="provider-integration-v1",
            provider_ids=tuple(self.list_providers()),
            version="1.0.0",
            preview_only=True,
            external_calls=0,
        )
