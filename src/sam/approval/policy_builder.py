"""
Policy Builder.

Constructs ApprovalPolicy from configuration dicts.
"""

from typing import Dict, Any, List
from .policy import ApprovalPolicy, PolicyEffect, PolicyCondition


class PolicyBuilder:
    @staticmethod
    def build(policy_id: str, name: str, effect: str, conditions: List[Dict[str, str]], owner: str = "") -> ApprovalPolicy:
        try:
            pe = PolicyEffect[effect.upper()]
        except KeyError:
            pe = PolicyEffect.DENY
        conds = [PolicyCondition(**c) for c in conditions]
        return ApprovalPolicy(policy_id=policy_id, name=name, effect=pe, conditions=conds, owner=owner)

    @staticmethod
    def default_policies() -> List[ApprovalPolicy]:
        return [
            ApprovalPolicy(policy_id="POL-HIGH-RISK", name="High Risk", effect=PolicyEffect.REQUIRE_REVIEW,
                conditions=[PolicyCondition(field="readiness_score", operator="lt", value="0.5")]),
            ApprovalPolicy(policy_id="POL-CERT-REQUIRED", name="Certification Required", effect=PolicyEffect.REQUIRE_REVIEW,
                conditions=[PolicyCondition(field="certified", operator="eq", value="False")]),
            ApprovalPolicy(policy_id="POL-AUTO-APPROVE", name="Auto Approve", effect=PolicyEffect.ALLOW,
                conditions=[PolicyCondition(field="readiness_score", operator="gt", value="0.8"),
                           PolicyCondition(field="certified", operator="eq", value="True")]),
        ]
