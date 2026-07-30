"""
Policy Validator.

Validates policy definitions for correctness.
"""

from typing import List, Tuple
from .policy import ApprovalPolicy, PolicyCondition


class PolicyValidator:
    @staticmethod
    def validate(policy: ApprovalPolicy) -> Tuple[bool, List[str]]:
        errors = []
        if not policy.policy_id: errors.append("Missing policy_id")
        if not policy.name: errors.append("Missing name")
        for i, c in enumerate(policy.conditions):
            if not c.field: errors.append(f"Condition #{i}: missing field")
            if c.operator not in ("eq","ne","gt","lt","in","contains"):
                errors.append(f"Condition #{i}: unknown operator '{c.operator}'")
        return (len(errors) == 0, errors)
