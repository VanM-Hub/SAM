"""Connector Router — engine routing permintaan ke connector.

Sprint 117 — Connector Routing.
Routing memilih connector untuk sebuah kebutuhan (read-only, deterministik).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .connector_registry import ConnectorRegistry
from .capability_selector import CapabilitySelector


@dataclass(frozen=True)
class RoutingPolicy:
    """Kebijakan routing (deterministik)."""
    policy_id: str
    strategy: str = "capability"  # capability | round_robin | first
    preferred_types: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class RoutingResult:
    """Hasil routing."""
    capability_name: str
    selected_connector_id: str = ""
    policy_id: str = ""
    routed: bool = False
    message: str = ""


class ConnectorRouter:
    """Router connector berdasarkan kapabilitas."""

    def __init__(self, registry: ConnectorRegistry) -> None:
        self._registry = registry
        self._selector = CapabilitySelector(registry)

    def route(self, capability_name: str, policy: RoutingPolicy) -> RoutingResult:
        sel = self._selector.select(capability_name)
        if sel.count == 0:
            return RoutingResult(capability_name, routed=False,
                                 message="no connector supports capability")
        # strategy capability: pilih first yang cocok (deterministik, sorted)
        # jika preferred_types diminta, filter dulu
        candidates = []
        for cid in sel.selected_connectors:
            d = self._registry.get(cid)
            if policy.preferred_types and d:
                if d.connector_type in policy.preferred_types:
                    candidates.append(cid)
            else:
                candidates.append(cid)
        if not candidates:
            return RoutingResult(capability_name, policy_id=policy.policy_id,
                                 routed=False, message="no preferred type matched")
        chosen = sorted(candidates)[0]
        return RoutingResult(capability_name, chosen, policy.policy_id, True, "routed")
