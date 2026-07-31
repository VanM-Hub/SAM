"""Provider Routing — routing request ke provider (read-only).

Sprint 152 — Provider Routing.
Memilih provider untuk operasi tertentu. Tidak invoke.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from ..registry.provider_registry import ProviderRegistry


@dataclass(frozen=True)
class RoutingRule:
    """Aturan routing (immutable)."""
    operation: str
    provider_type: Optional[str] = None
    provider_id: Optional[str] = None


@dataclass(frozen=True)
class RoutingDecision:
    """Keputusan routing (immutable)."""
    operation: str
    provider_id: Optional[str] = None
    matched: bool = False
    candidates: List[str] = field(default_factory=list)


class ProviderRouter:
    """Router provider. Deterministik, read-only."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry
        self._rules: List[RoutingRule] = []

    def add_rule(self, rule: RoutingRule) -> None:
        self._rules.append(rule)

    def route(self, operation: str) -> RoutingDecision:
        # 1. by provider_id
        for rule in self._rules:
            if rule.operation == operation and rule.provider_id:
                if self._registry.get(rule.provider_id):
                    return RoutingDecision(
                        operation=operation, provider_id=rule.provider_id, matched=True
                    )
        # 2. by provider_type
        for rule in self._rules:
            if rule.operation == operation and rule.provider_type:
                found = [
                    pid for pid in self._registry.list_ids()
                    if self._registry.get(pid)
                    and self._registry.get(pid).provider_type == rule.provider_type
                    and self._registry.get_capabilities(pid)
                    and any(c.supports(operation) for c in self._registry.get_capabilities(pid))
                ]
                if found:
                    return RoutingDecision(
                        operation=operation,
                        provider_id=found[0],
                        matched=True,
                        candidates=found,
                    )
        # 3. capability-based fallback
        candidates = [
            pid for pid in self._registry.list_ids()
            if any(c.supports(operation) for c in self._registry.get_capabilities(pid))
        ]
        return RoutingDecision(
            operation=operation,
            provider_id=candidates[0] if candidates else None,
            matched=bool(candidates),
            candidates=candidates,
        )
