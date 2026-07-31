"""Provider Dispatcher (Sprint 253).

Program C - Real Execution Runtime.
Dispatcher memilih provider TANPA provider-specific logic. Semua melalui
abstraksi adapter; eksekusi aktual (network) hanya saat execute+approved.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional

from .execution_request import ExecutionRequest

KNOWN_PROVIDERS = (
    "filesystem", "shell", "sqlite", "docker", "openclaw",
    "openai", "anthropic", "gemini", "deepseek", "ollama",
)


@dataclass(frozen=True)
class DispatchTarget:
    """Target dispatch (immutable)."""
    provider_id: str
    operation: str
    mode: str = "preview"
    available: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "provider_id": self.provider_id,
            "operation": self.operation,
            "mode": self.mode,
            "available": self.available,
            "external_calls": self.external_calls,
        }


class ProviderDispatcher:
    """Dispatcher provider. Routing generik via interface, no network."""

    def __init__(self) -> None:
        self._providers: Dict[str, object] = {}
        self._known = set(KNOWN_PROVIDERS)

    def register(self, provider: str, adapter: object) -> None:
        self._providers[provider] = adapter

    def is_known(self, provider: str) -> bool:
        return provider in self._known

    def dispatch(self, request: ExecutionRequest) -> DispatchTarget:
        if not self.is_known(request.provider_id):
            raise ValueError(f"unknown provider: {request.provider_id}")
        return DispatchTarget(
            provider_id=request.provider_id,
            operation=request.operation,
            mode=request.mode,
            available=request.provider_id in self._providers,
            external_calls=0,
        )
