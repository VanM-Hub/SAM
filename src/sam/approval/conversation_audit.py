"""Audit Conversation Bridge."""
from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

class ConversationAuditBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def query_count(self)->int:return 6
    @property
    def _engine(self):return self._runtime._audit_engine
    def get_log(self)->Dict[str,Any]:return {"query":"audit_log","entries":[e.to_dict() for e in self._engine.get_log().entries]}
    def filter_action(self,action:str)->Dict[str,Any]:
        es=[e.to_dict() for e in self._engine.filter_by_action(action)]
        return {"query":"filter_action","action":action,"count":len(es),"entries":es}
    def filter_actor(self,actor:str)->Dict[str,Any]:
        es=[e.to_dict() for e in self._engine.filter_by_actor(actor)]
        return {"query":"filter_actor","actor":actor,"count":len(es),"entries":es}
    def stats(self)->Dict[str,Any]:return {"query":"audit_stats","total":self._engine.entry_count}
