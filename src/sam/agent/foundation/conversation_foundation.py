"""Conversation Foundation Bridge — query read-only (Sprint 156).

Agent Runtime — query read-only. Tidak memodifikasi runtime.
"""
from __future__ import annotations
from typing import List

from .agent_registry import AgentRegistry


class ConversationFoundationBridge:
    """Bridge conversation — ringkasan agent read-only."""

    def __init__(self, registry: AgentRegistry) -> None:
        self._registry = registry

    def show_agent_status(self) -> dict:
        return {"registered": self._registry.count()}

    def list_agents(self) -> List[str]:
        return self._registry.list_ids()

    def describe(self, agent_id: str) -> str:
        desc = self._registry.get(agent_id)
        return desc.name if desc else f"agent {agent_id} not found"

    def count(self) -> int:
        return self._registry.count()

    def capability_names(self, agent_id: str) -> List[str]:
        return [c.capability_id for c in self._registry.get_capabilities(agent_id)]
