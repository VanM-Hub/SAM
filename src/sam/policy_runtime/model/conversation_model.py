"""Conversation Model Bridge — query read-only (Sprint 205)."""
from __future__ import annotations

from .policy import Policy
from .policy_rule import PolicyRule
from .policy_scope import PolicyScope
from .policy_constraint import PolicyConstraint
from .policy_validator import PolicyValidator


class ConversationModelBridge:
    """Bridge conversation — query model policy read-only."""

    def __init__(self) -> None:
        self._validator = PolicyValidator()

    def build_policy(self, policy_id: str, name: str = "") -> Policy:
        return Policy(policy_id=policy_id, name=name)

    def build_rule(self, rule_id: str, policy_id: str) -> PolicyRule:
        return PolicyRule(rule_id=rule_id, policy_id=policy_id)

    def is_valid(self, policy: Policy) -> bool:
        return self._validator.validate_policy(policy).valid

    def summary(self, policy: Policy) -> dict:
        return {
            "policy_id": policy.policy_id,
            "rule_count": policy.rule_count(),
        }
