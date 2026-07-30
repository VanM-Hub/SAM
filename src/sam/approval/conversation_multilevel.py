"""Multi-Level Conversation Bridge."""
from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1

class ConversationMultiLevelBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None:self._runtime=runtime
    @property
    def query_count(self)->int:return 10
    @property
    def _engine(self):return self._runtime._multilevel_engine
    def list_approvals(self)->Dict[str,Any]:
        return {"query":"list_approvals","count":self._engine.approval_count}
    def approval_by_id(self,aid:str)->Dict[str,Any]:
        m=self._engine.get(aid);return {"query":"approval_by_id","found":m is not None,"approval":m.to_dict() if m else {}}
    def current_level(self,aid:str)->Dict[str,Any]:
        c=self._engine.current_level(aid);return {"query":"current_level","level":c.to_dict() if c else None}
    def status(self,aid:str)->Dict[str,Any]:
        s=self._engine.get_status(aid);return {"query":"level_status","status":[x.to_dict() for x in s] if s else []}
    def engine_stats(self)->Dict[str,Any]:return {"query":"engine_stats","approval_count":self._engine.approval_count}
    def levels_info(self)->Dict[str,Any]:
        return {"query":"levels_info","default_levels":["Team Lead","Manager","Director"],"max_levels":10}
    def summary(self)->Dict[str,Any]:return {"query":"summary","active":self._engine.approval_count,"engine":"active"}
    def completed_count(self)->Dict[str,Any]:
        c=sum(1 for m in [self._engine.get(aid) for aid in list(self._engine._approvals.keys())] if m and m.completed)
        return {"query":"completed_count","count":c}
    def pending_count(self)->Dict[str,Any]:
        p=sum(1 for m in [self._engine.get(aid) for aid in list(self._engine._approvals.keys())] if m and not m.completed)
        return {"query":"pending_count","count":p}
    def all_summary(self)->Dict[str,Any]:
        return {"query":"all_summary","total":self._engine.approval_count}
