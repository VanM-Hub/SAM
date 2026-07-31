"""Dashboard Provider Bridge — bridge read-only untuk dashboard.

Sprint 144 — Provider Foundation (OP-1407).
Menghasilkan ExecutionCard frozen untuk tiap provider. Read-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..registry.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class ExecutionCard:
    """Kartu eksekusi frozen untuk dashboard (read-only)."""
    provider_id: str
    provider_type: str = "generic"
    state: str = "unknown"
    summary: str = ""
    detail: str = ""
    verdict: str = "pending"


class DashboardProviderBridge:
    """Bridge dashboard — menghasilkan ExecutionCard per provider."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry

    def cards(self) -> List[ExecutionCard]:
        cards = []
        for pid in self._registry.list_ids():
            desc = self._registry.get(pid)
            status = self._registry.get_status(pid)
            caps = self._registry.get_capabilities(pid)
            card = ExecutionCard(
                provider_id=pid,
                provider_type=desc.provider_type if desc else "generic",
                state=status.state if status else "unknown",
                summary=f"{pid}: {len(caps)} capability(s)",
                detail=desc.description if desc else "",
                verdict="ready" if (status and status.registered) else "pending",
            )
            cards.append(card)
        return cards

    def card(self, provider_id: str) -> ExecutionCard:
        for c in self.cards():
            if c.provider_id == provider_id:
                return c
        return ExecutionCard(
            provider_id=provider_id,
            state="not-found",
            verdict="missing",
        )
