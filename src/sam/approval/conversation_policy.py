"""
Policy Conversation Bridge.
"""

from typing import Dict,Any,TYPE_CHECKING,List
from .policy import PolicyEffect
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

class ConversationPolicyBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10
    @property
    def _engine(self): return self._runtime._policy_engine
    def list_policies(self)->Dict[str,Any]:
        ps=[p.to_dict() for p in self._engine.list_policies()]
        return {"query":"list_policies","count":len(ps),"policies":ps}
    def policy_by_id(self,pid:str)->Dict[str,Any]:
        p=self._engine.get(pid);return {"query":"policy_by_id","found":p is not None,"policy":p.to_dict() if p else {}}
    def evaluate(self,pid:str,context:Dict[str,Any])->Dict[str,Any]:
        r=self._engine.evaluate(pid,context);return {"query":"evaluate_policy","result":r.to_dict()}
    def evaluate_all(self,context:Dict[str,Any])->Dict[str,Any]:
        rs=[r.to_dict() for r in self._engine.evaluate_all(context)]
        return {"query":"evaluate_all","count":len(rs),"results":rs}
    def engine_stats(self)->Dict[str,Any]:return {"query":"engine_stats","policy_count":self._engine.policy_count}
    def effects(self)->Dict[str,Any]:return {"query":"effects","effects":[e.name for e in PolicyEffect]}
    def default_policies_summary(self)->Dict[str,Any]:
        from .policy_builder import PolicyBuilder
        return {"query":"default_policies","count":len(PolicyBuilder.default_policies())}
    def policy_names(self)->Dict[str,Any]:return {"query":"policy_names","names":[p.name for p in self._engine.list_policies()]}
    def policy_stats(self)->Dict[str,Any]:return {"query":"policy_stats",
        "total":self._engine.policy_count,
        "allow":sum(1 for p in self._engine.list_policies() if p.effect==PolicyEffect.ALLOW),
        "deny":sum(1 for p in self._engine.list_policies() if p.effect==PolicyEffect.DENY)}
    def summary(self)->Dict[str,Any]:return {"query":"policy_summary","engine_status":"active" if self._engine else "inactive"}
