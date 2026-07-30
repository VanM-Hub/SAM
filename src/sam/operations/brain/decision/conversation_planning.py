"""
Decision Runtime Conversation Planning Bridge.

10 DTO-only queries for decision planning.
"""

from typing import Dict,Any,TYPE_CHECKING
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

class DecisionConversationPlanningBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def query_count(self)->int: return 10
    def latest_plan(self)->Dict[str,Any]:
        l=self._runtime._latest_plan
        return {"query":"latest_plan","has_plan":l is not None,"plan":l.to_dict() if l else None}
    def alternatives(self)->Dict[str,Any]:
        l=self._runtime._latest_plan
        return {"query":"alternatives","count":len(l.alternatives) if l else 0,
                "alternatives":[a.to_dict() for a in l.alternatives] if l else []}
    def strategy(self)->Dict[str,Any]:
        l=self._runtime._latest_plan
        return {"query":"strategy","strategy":l.strategy if l else {}}
    def constraints(self)->Dict[str,Any]:
        l=self._runtime._latest_plan
        return {"query":"constraints","constraints":l.constraints if l else {}}
    def planning_summary(self)->Dict[str,Any]:
        return {"query":"planning_summary","total":self._runtime._plan_count,"has_latest":self._runtime._latest_plan is not None}
    def planning_history(self,limit:int=50)->Dict[str,Any]:
        return {"query":"planning_history","total":self._runtime._plan_count}
    def statistics(self)->Dict[str,Any]:
        return {"query":"statistics","total":self._runtime._plan_count}
    def blocked_constraints(self)->Dict[str,Any]:
        l=self._runtime._latest_plan
        cons=l.constraints if l else {}
        return {"query":"blocked_constraints","blocked":cons.get("blocked",False) if cons else False}
    def recommended_alternative(self)->Dict[str,Any]:
        l=self._runtime._latest_plan
        return {"query":"recommended_alternative","recommended":l.recommended.to_dict() if l and l.recommended else None}
    def planning_readiness(self)->Dict[str,Any]:
        l=self._runtime._latest_plan;r=l.recommended if l else None
        return {"query":"planning_readiness","ready":r.readiness if r else "UNKNOWN"}
