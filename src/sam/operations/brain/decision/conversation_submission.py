"""
Decision Runtime Conversation Submission Bridge.

10 DTO-only queries for submission orchestration.
"""

from typing import Dict,Any,TYPE_CHECKING
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationSubmissionBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def query_count(self)->int: return 10
    def submission_plan(self)->Dict[str,Any]:
        l=self._runtime._latest_submission
        return {"query":"submission_plan","has_plan":l is not None,"plan":l.to_dict() if l else None}
    def submission_queue(self)->Dict[str,Any]:
        q=self._runtime._submission_queue
        return {"query":"submission_queue","queue":q.to_dict() if q else {"total":0}}
    def dependencies(self)->Dict[str,Any]:
        l=self._runtime._latest_submission; d=l.metadata.depends_on if l and l.metadata else []
        return {"query":"dependencies","dependencies":d}
    def priority(self)->Dict[str,Any]:
        l=self._runtime._latest_submission; p=l.metadata.priority if l and l.metadata else 0
        return {"query":"priority","priority":p}
    def validation(self)->Dict[str,Any]:
        from .submission_validator import SubmissionValidator
        l=self._runtime._latest_submission
        if not l: return {"query":"validation","valid":True}
        r=SubmissionValidator().validate(l); return {"query":"validation","result":r.to_dict()}
    def summary(self)->Dict[str,Any]:
        from .submission_summary import SubmissionSummaryBuilder
        l=self._runtime._latest_submission
        return {"query":"summary","summary":SubmissionSummaryBuilder().build(l) if l else {}}
    def statistics(self)->Dict[str,Any]:
        return {"query":"statistics","total":self._runtime._submission_count}
    def blocking_issues(self)->Dict[str,Any]:
        l=self._runtime._latest_submission
        issues=[]; 
        if l and not l.ready: issues.append("Plan not ready for submission")
        return {"query":"blocking_issues","issues":issues}
    def approval_readiness(self)->Dict[str,Any]:
        l=self._runtime._latest_submission
        return {"query":"approval_readiness","ready":l.ready if l else False}
    def history(self,limit:int=50)->Dict[str,Any]:
        return {"query":"history","total":self._runtime._submission_count}
