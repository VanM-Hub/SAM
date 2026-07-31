"""Conversation LLM Bridge — bridge read-only untuk LLM adapter (Sprint 229)."""
from __future__ import annotations
from typing import List, Optional

from .llm_adapter import LLMAdapter
from .llm_model import LLMModel


class ConversationLLMBridge:
    """Bridge conversation — query read-only ke adapter/model LLM."""

    def __init__(self, adapter: Optional[LLMAdapter] = None) -> None:
        self._adapter = adapter

    def attach(self, adapter: LLMAdapter) -> None:
        self._adapter = adapter

    def provider_id(self) -> Optional[str]:
        return self._adapter.provider_id if self._adapter else None

    def list_models(self) -> List[str]:
        if not self._adapter:
            return []
        return [m.model_id for m in self._adapter.models()]

    def describe_model(self, model_id: str) -> Optional[LLMModel]:
        if not self._adapter:
            return None
        for m in self._adapter.models():
            if m.model_id == model_id:
                return m
        return None

    def count_models(self) -> int:
        if not self._adapter:
            return 0
        return len(self._adapter.models())
