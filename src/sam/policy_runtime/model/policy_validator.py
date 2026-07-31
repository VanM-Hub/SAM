"""Policy Validator — validasi model policy (Sprint 205)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .policy import Policy
from .policy_rule import PolicyRule
from .policy_scope import PolicyScope, VALID_SCOPES
from .policy_constraint import PolicyConstraint


@dataclass(frozen=True)
class PolicyValidation:
    """Hasil validasi (immutable)."""
    valid: bool = True
    issues: List[str] = field(default_factory=list)


class PolicyValidator:
    """Validator model policy. Deterministik, read-only."""

    def validate_policy(self, policy: Policy) -> PolicyValidation:
        issues = []
        if not policy.policy_id:
            issues.append("policy_id is required")
        return PolicyValidation(valid=not issues, issues=issues)

    def validate_rule(self, rule: PolicyRule) -> PolicyValidation:
        issues = []
        if not rule.rule_id:
            issues.append("rule_id is required")
        return PolicyValidation(valid=not issues, issues=issues)

    def validate_scope(self, scope: PolicyScope) -> PolicyValidation:
        issues = []
        if scope.scope not in VALID_SCOPES:
            issues.append(f"invalid scope '{scope.scope}'")
        return PolicyValidation(valid=not issues, issues=issues)

    def validate_constraint(self, constraint: PolicyConstraint) -> PolicyValidation:
        issues = []
        if not constraint.constraint_id:
            issues.append("constraint_id is required")
        return PolicyValidation(valid=not issues, issues=issues)
