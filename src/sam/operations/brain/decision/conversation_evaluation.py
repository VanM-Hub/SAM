"""
Decision Runtime Conversation Evaluation Bridge.

10 DTO-only queries for decision evaluation.
"""

from typing import Dict,Any,TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationEvaluationBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def query_count(self)->int: return 10
    def evaluation(self)->Dict[str,Any]:
        l=self._runtime._latest_evaluation
        return {"query":"evaluation","has_evaluation":l is not None,"evaluation":l.to_dict() if l else None}
    def readiness(self)->Dict[str,Any]:
        l=self._runtime._latest_evaluation
        return {"query":"readiness","ready":l.ready if l else "UNKNOWN"}
    def confidence(self)->Dict[str,Any]:
        l=self._runtime._latest_evaluation
        return {"query":"confidence","level":l.confidence if l else "UNKNOWN"}
    def policy(self)->Dict[str,Any]:
        l=self._runtime._latest_evaluation
        return {"query":"policy","result":l.policy_result.to_dict() if l and l.policy_result else {}}
    def risk(self)->Dict[str,Any]:
        l=self._runtime._latest_evaluation
        if not l or not l.readiness_result: return {"query":"risk","score":0}
        return {"query":"risk","score":l.readiness_result.score,"warnings":l.readiness_result.warnings}
    def summary(self)->Dict[str,Any]:
        l=self._runtime._latest_evaluation
        return {"query":"summary","evaluations_count":self._runtime._evaluation_count,"latest":l.to_dict() if l else None}
    def history(self,limit:int=50)->Dict[str,Any]:
        return {"query":"history","total":self._runtime._evaluation_count}
    def blocked(self)->Dict[str,Any]:
        return {"query":"blocked","blocked_count":self._runtime._blocked_count}
    def warnings(self)->Dict[str,Any]:
        l=self._runtime._latest_evaluation
        all_w=[];r=l.readiness_result if l else None;p=l.policy_result if l else None
        if r: all_w.extend(r.warnings)
        if p: all_w.extend(p.warnings)
        return {"query":"warnings","warnings":all_w}
    def statistics(self)->Dict[str,Any]:
        return {"query":"statistics","evaluated":self._runtime._evaluation_count,"ready":self._runtime._ready_count}
