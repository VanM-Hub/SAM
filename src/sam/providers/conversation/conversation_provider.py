"""Conversation Provider Bridge — bridge read-only untuk konsumsi internal.

Sprint 144 — Provider Foundation (OP-1406).
Mengakses registry secara read-only. Tidak memodifikasi apa pun.
"""
from __future__ import annotations
from typing import List, Optional

from ..registry.provider_registry import ProviderRegistry
from ..base.provider_descriptor import (
    ProviderDescriptor,
    ProviderStatus,
    ProviderSummary,
)


class ConversationProviderBridge:
    """Bridge conversation — query read-only ke ProviderRegistry."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def describe(self) -> ProviderSummary:
        return self._registry.summary()

    def list_providers(self) -> List[str]:
        return self._registry.list_ids()

    def get(self, provider_id: str) -> Optional[ProviderDescriptor]:
        return self._registry.get(provider_id)

    def status(self, provider_id: str) -> Optional[ProviderStatus]:
        return self._registry.get_status(provider_id)

    def capabilities(self, provider_id: str) -> List[str]:
        return [
            c.name for c in self._registry.get_capabilities(provider_id)
        ]

    def count(self) -> int:
        return self._registry.count()
