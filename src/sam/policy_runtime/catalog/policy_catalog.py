"""Policy Catalog — katalog policy read-only (Sprint 208).

Tidak load file, tidak cache. Register hanya komposisi in-memory.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Dict

from ..model.policy import Policy


@dataclass(frozen=True)
class PolicyCatalogEntry:
    """Entri katalog (immutable)."""
    policy_id: str
    rule_count: int = 0


class PolicyCatalog:
    """Katalog policy in-memory. Register hanya komposisi (no write/no file)."""

    def __init__(self) -> None:
        self._policies: Dict[str, Policy] = {}

    def add(self, policy: Policy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: str) -> Policy | None:
        return self._policies.get(policy_id)

    def all_entries(self) -> List[PolicyCatalogEntry]:
        return [
            PolicyCatalogEntry(policy_id=pol.policy_id, rule_count=pol.rule_count())
            for pol in self._policies.values()
        ]

    def count(self) -> int:
        return len(self._policies)

    def by_scope(self, scope: str) -> List[Policy]:
        return [pol for pol in self._policies.values() if pol.scope == scope]
