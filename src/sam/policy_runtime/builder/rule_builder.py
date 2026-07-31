"""Rule Builder — membangun PolicyRule (Sprint 206)."""
from __future__ import annotations

from ..model.policy_rule import PolicyRule


class RuleBuilder:
    """Builder aturan. Menyusun DTO deklaratif saja — tidak mengevaluasi."""

    def build(self, rule_id: str, policy_id: str, kind: str = "allow") -> PolicyRule:
        return PolicyRule(rule_id=rule_id, policy_id=policy_id, kind=kind)
