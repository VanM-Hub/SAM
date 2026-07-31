"""Policy Index — indeks policy (Sprint 208)."""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..model.policy_rule import PolicyRule
from ..model.policy import Policy


@dataclass(frozen=True)
class PolicyIndex:
    """Indeks policy (immutable)."""
    policy_id: str = ""
    rule_count: int = 0
    rule_ids: tuple = ()

    def has_rule(self, rule_id: str) -> bool:
        return rule_id in self.rule_ids


class PolicyIndexer:
    """Indexer policy. Read-only, deterministik."""

    def index(self, policy: Policy, rules: List[PolicyRule]) -> PolicyIndex:
        return PolicyIndex(
            policy_id=policy.policy_id,
            rule_count=policy.rule_count(),
            rule_ids=tuple(r.rule_id for r in rules),
        )

    def search(self, index: PolicyIndex, term: str) -> List[str]:
        return [rid for rid in index.rule_ids if term in rid]
