"""Delegation Conversation Bridge."""
from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

class ConversationDelegationBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def query_count(self)->int:return 6
    @property
    def _engine(self):return self._runtime._delegation_engine
    def list_rules(self)->Dict[str,Any]:
        rs=[r.to_dict() for r in self._engine.list_active()]
        return {"query":"list_rules","count":len(rs),"rules":rs}
    def resolve(self,user:str)->Dict[str,Any]:
        resolved=self._engine.resolve(user)
        return {"query":"resolve","original":user,"resolved":resolved,"delegated":resolved!=user}
    def stats(self)->Dict[str,Any]:
        return {"query":"delegation_stats","total":self._engine.rule_count,"active":len(self._engine.list_active())}
