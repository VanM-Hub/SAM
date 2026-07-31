"""Conversation Binding — bridge read-only untuk binding.

Sprint 115 — Connector Binding.
Query read-only ke binding registry. Tidak ada mutasi dari bridge.
"""
from __future__ import annotations
from typing import List, Optional

from .binding_registry import BindingRegistry
from .binding_result import BindingResult


class ConversationBindingBridge:
    """Bridge conversation binding — read-only."""

    def __init__(self, binding_registry: BindingRegistry) -> None:
        self._registry = binding_registry

    def get(self, binding_id: str) -> Optional[BindingResult]:
        return self._registry.get(binding_id)

    def list(self) -> List[BindingResult]:
        return self._registry.list_bindings()

    def count(self) -> int:
        return self._registry.count()
