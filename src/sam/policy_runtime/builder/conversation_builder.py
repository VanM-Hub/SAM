"""Conversation Builder Bridge — query read-only (Sprint 206)."""
from __future__ import annotations

from ..model.policy import Policy
from .policy_builder import PolicyBuilder
from .rule_builder import RuleBuilder
from .scope_builder import ScopeBuilder
from .constraint_builder import ConstraintBuilder
from .preview_builder import PreviewBuilder


class ConversationBuilderBridge:
    """Bridge conversation — 5 query read-only builder policy."""

    def __init__(self) -> None:
        self._pol = PolicyBuilder()
        self._rule = RuleBuilder()
        self._scope = ScopeBuilder()
        self._cst = ConstraintBuilder()
        self._prev = PreviewBuilder()

    def query_1_policy(self, policy_id: str) -> Policy:
        return self._pol.build(policy_id).policy

    def query_2_rule(self, rule_id: str, policy_id: str):
        return self._rule.build(rule_id, policy_id)

    def query_3_scope(self, scope: str):
        return self._scope.build(scope)

    def query_4_constraint(self, constraint_id: str):
        return self._cst.build(constraint_id)

    def query_5_preview(self, label: str, policy: Policy):
        return self._prev.build(label, policy)
