"""
Policy Engine.

Evaluates ApprovalPolicy against approval contexts.
"""

from typing import List, Dict, Any, Optional
from .policy import ApprovalPolicy, PolicyEffect, PolicyCondition, PolicyEvaluationResult


class PolicyEngine:
    def __init__(self) -> None:
        self._policies: Dict[str, ApprovalPolicy] = {}

    @property
    def policy_count(self) -> int: return len(self._policies)

    def register(self, policy: ApprovalPolicy) -> None:
        self._policies[policy.policy_id] = policy

    def get(self, policy_id: str) -> Optional[ApprovalPolicy]:
        return self._policies.get(policy_id)

    def evaluate(self, policy_id: str, context: Dict[str, Any]) -> PolicyEvaluationResult:
        policy = self._policies.get(policy_id)
        if not policy:
            return PolicyEvaluationResult(policy_id=policy_id, effect=PolicyEffect.ALLOW, match=False, reason="Policy not found")

        if not policy.conditions:
            return PolicyEvaluationResult(policy_id=policy_id, effect=policy.effect, match=True, reason="No conditions")

        matches = [self._match_condition(c, context) for c in policy.conditions]
        if all(matches):
            return PolicyEvaluationResult(policy_id=policy_id, effect=policy.effect, match=True, reason="All conditions matched")
        else:
            return PolicyEvaluationResult(policy_id=policy_id, effect=PolicyEffect.ALLOW, match=False, reason="Conditions not met")

    def evaluate_all(self, context: Dict[str, Any]) -> List[PolicyEvaluationResult]:
        results = []
        for pid in self._policies:
            r = self.evaluate(pid, context)
            if r.match:
                results.append(r)
        return results

    def list_policies(self) -> List[ApprovalPolicy]:
        return list(self._policies.values())

    @staticmethod
    def _match_condition(condition: PolicyCondition, context: Dict[str, Any]) -> bool:
        val = context.get(condition.field)
        if val is None:
            return False
        sv = str(val)
        cv = condition.value
        op = condition.operator
        if op == "eq": return sv == cv
        if op == "ne": return sv != cv
        if op == "gt": return sv > cv
        if op == "lt": return sv < cv
        if op == "in": return sv in [x.strip() for x in cv.split(",")]
        if op == "contains": return cv in sv
        return False
