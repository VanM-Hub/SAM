"""
Policy Dashboard Bridge.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
from .policy import PolicyEffect
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

@dataclass(frozen=True)
class PolicyCard:
    policy_id:str; name:str; effect:str; timestamp:float
    def to_dict(self)->Dict[str,Any]:return {"card":"Policy","policy_id":self.policy_id,"name":self.name,"effect":self.effect,"timestamp":self.timestamp}
@dataclass(frozen=True)
class EngineCard:
    policy_count:int; has_policies:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]:return {"card":"PolicyEngine","policy_count":self.policy_count,"has_policies":self.has_policies,"timestamp":self.timestamp}
@dataclass(frozen=True)
class DistributionCard:
    allow:int; deny:int; review:int; total:int; timestamp:float
    def to_dict(self)->Dict[str,Any]:return {"card":"PolicyDistribution","allow":self.allow,"deny":self.deny,"review":self.review,"total":self.total,"timestamp":self.timestamp}

class DashboardPolicyBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def card_count(self)->int:return 3
    @property
    def _engine(self):return self._runtime._policy_engine

    def get_policy_card(self,pid:str)->PolicyCard:
        p=self._engine.get(pid);return PolicyCard(policy_id=p.policy_id if p else "",name=p.name if p else "",effect=p.effect.name if p else "NONE",timestamp=datetime.now().timestamp())
    def get_engine_card(self)->EngineCard:return EngineCard(policy_count=self._engine.policy_count,has_policies=self._engine.policy_count>0,timestamp=datetime.now().timestamp())
    def get_distribution_card(self)->DistributionCard:
        a=sum(1 for p in self._engine.list_policies() if p.effect==PolicyEffect.ALLOW)
        d=sum(1 for p in self._engine.list_policies() if p.effect==PolicyEffect.DENY)
        r=sum(1 for p in self._engine.list_policies() if p.effect==PolicyEffect.REQUIRE_REVIEW)
        return DistributionCard(allow=a,deny=d,review=r,total=self._engine.policy_count,timestamp=datetime.now().timestamp())
    def get_all_cards(self)->Dict[str,Any]:return {"engine":self.get_engine_card().to_dict(),"distribution":self.get_distribution_card().to_dict()}
