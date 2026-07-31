"""Dashboard LLM Bridge — bridge read-only untuk dashboard (Sprint 229)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .llm_adapter import LLMAdapter


@dataclass(frozen=True)
class LLMCard:
    """Kartu LLM frozen untuk dashboard (read-only)."""
    provider_id: str
    model_count: int = 0
    state: str = "unknown"
    summary: str = ""
    verdict: str = "pending"


class DashboardLLMBridge:
    """Bridge dashboard — menghasilkan LLMCard per adapter."""

    def __init__(self, adapter: Optional[LLMAdapter] = None) -> None:
        self._adapter = adapter

    def attach(self, adapter: LLMAdapter) -> None:
        self._adapter = adapter

    def card(self) -> LLMCard:
        if not self._adapter:
            return LLMCard(provider_id="none", model_count=0, state="not-found")
        models = self._adapter.models()
        return LLMCard(
            provider_id=self._adapter.provider_id,
            model_count=len(models),
            state="ready",
            summary=f"{self._adapter.provider_id}: {len(models)} model(s)",
            verdict="ready",
        )

    def available(self) -> bool:
        return self._adapter is not None
