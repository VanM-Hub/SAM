"""
Decision Runtime Conversation Approval Bridge.

10 DTO-only queries for approval preparation.
"""

from typing import Dict,Any,TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationApprovalBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def query_count(self)->int: return 10

    def approval_package(self)->Dict[str,Any]:
        l=self._runtime._latest_approval
        return {"query":"approval_package","has_package":l is not None,"package":l.to_dict() if l else None}
    def requirements(self)->Dict[str,Any]:
        l=self._runtime._latest_approval
        reqs=[r.to_dict() for r in l.requirements] if l else []
        return {"query":"requirements","total":len(reqs),"requirements":reqs}
    def missing_items(self)->Dict[str,Any]:
        l=self._runtime._latest_approval
        missing=[r.name for r in l.requirements if not r.satisfied] if l else []
        return {"query":"missing_items","missing":missing}
    def validation(self)->Dict[str,Any]:
        from .approval_validator import ApprovalValidator
        l=self._runtime._latest_approval
        if not l: return {"query":"validation","valid":True}
        r=ApprovalValidator().validate(l)
        return {"query":"validation","result":r.to_dict()}
    def summary(self)->Dict[str,Any]:
        from .approval_summary import ApprovalSummaryBuilder
        l=self._runtime._latest_approval
        return {"query":"summary","summary":ApprovalSummaryBuilder().build(l) if l else {}}
    def statistics(self)->Dict[str,Any]:
        return {"query":"statistics","total":self._runtime._approval_count,"ready":self._runtime._approval_ready_count}
    def readiness(self)->Dict[str,Any]:
        l=self._runtime._latest_approval
        return {"query":"readiness","ready":l.ready_for_submission if l else False}
    def constraints(self)->Dict[str,Any]:
        l=self._runtime._latest_approval
        return {"query":"constraints","missing":[r.name for r in l.requirements if not r.satisfied] if l else []}
    def recommendation(self)->Dict[str,Any]:
        from .approval_summary import ApprovalSummaryBuilder
        l=self._runtime._latest_approval
        if not l: return {"query":"recommendation","recommendation":"No approval prepared"}
        s=ApprovalSummaryBuilder().build(l)
        return {"query":"recommendation","recommendation":s.get("recommendation","")}
    def history(self,limit:int=50)->Dict[str,Any]:
        return {"query":"history","total":self._runtime._approval_count}
