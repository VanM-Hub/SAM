"""
Approval Policy Engine.
Defines approval policies and evaluates them against workflows.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Callable
from enum import Enum, auto


class PolicyEffect(Enum):
    ALLOW = auto()
    DENY = auto()
    REQUIRE_REVIEW = auto()


@dataclass(frozen=True)
class PolicyCondition:
    field: str = ""
    operator: str = "eq"
    value: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"field":self.field,"operator":self.operator,"value":self.value}


@dataclass(frozen=True)
class ApprovalPolicy:
    policy_id: str = ""
    name: str = ""
    effect: PolicyEffect = PolicyEffect.DENY
    conditions: List[PolicyCondition] = field(default_factory=list)
    owner: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"policy_id":self.policy_id,"name":self.name,
        "effect":self.effect.name,"owner":self.owner,"conditions":[c.to_dict() for c in self.conditions]}


@dataclass(frozen=True)
class PolicyEvaluationResult:
    policy_id: str = ""
    effect: PolicyEffect = PolicyEffect.ALLOW
    match: bool = False
    reason: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"policy_id":self.policy_id,"effect":self.effect.name,
        "match":self.match,"reason":self.reason}
