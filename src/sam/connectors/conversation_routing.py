"""Conversation Routing — bridge read-only untuk routing.

Sprint 117 — Connector Routing.
Query read-only ke router. Tidak ada mutasi.
"""
from __future__ import annotations
from typing import List

from .connector_registry import ConnectorRegistry
from .connector_router import ConnectorRouter, RoutingPolicy, RoutingResult


class ConversationRoutingBridge:
    """Bridge conversation routing — read-only."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._router = ConnectorRouter(registry)

    def route(self, capability_name: str, policy: RoutingPolicy = None) -> RoutingResult:
        policy = policy or RoutingPolicy("default")
        return self._router.route(capability_name, policy)

    def available_capabilities(self) -> List[str]:
        names = set()
        for cid in self._registry.list_ids():
            for cap in self._registry.get_capabilities(cid):
                names.add(cap.name)
        return sorted(names)
