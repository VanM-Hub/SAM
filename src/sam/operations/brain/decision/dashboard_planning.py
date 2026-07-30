"""
Decision Runtime Dashboard Planning Bridge.

6 immutable cards for decision planning.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

@dataclass(frozen=True)
class DecisionPlanCard:
    has_plan:bool; alternatives:int; recommended:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Decision Plan","has_plan":self.has_plan,"alternatives":self.alternatives,"recommended":self.recommended,"timestamp":self.timestamp}

@dataclass(frozen=True)
class AlternativesCard:
    total:int; top_scores:list; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Alternatives","total":self.total,"top_scores":list(self.top_scores),"timestamp":self.timestamp}

@dataclass(frozen=True)
class StrategyCard:
    approach:str; urgency:str; requires_approval:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Strategy","approach":self.approach,"urgency":self.urgency,"requires_approval":self.requires_approval,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ConstraintsCard:
    blocked:bool; total:int; blocked_count:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Constraints","blocked":self.blocked,"total":self.total,"blocked_count":self.blocked_count,"timestamp":self.timestamp}

@dataclass(frozen=True)
class PlanningStatusCard:
    plan_count:int; has_latest:bool; latest_ready:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Planning Status","plan_count":self.plan_count,"has_latest":self.has_latest,"latest_ready":self.latest_ready,"timestamp":self.timestamp}

@dataclass(frozen=True)
class StatisticsCard:
    total:int; total_alternatives:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"total_alternatives":self.total_alternatives,"timestamp":self.timestamp}


class DecisionDashboardPlanningBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_decision_plan_card(self)->DecisionPlanCard:
        l=self._runtime._latest_plan
        return DecisionPlanCard(has_plan=l is not None,alternatives=len(l.alternatives) if l else 0,
            recommended=l.recommended.action_type if l and l.recommended else "none",timestamp=datetime.now().timestamp())

    def get_alternatives_card(self)->AlternativesCard:
        l=self._runtime._latest_plan
        scores=[a.score for a in l.alternatives] if l else []
        return AlternativesCard(total=len(scores),top_scores=scores[:5],timestamp=datetime.now().timestamp())

    def get_strategy_card(self)->StrategyCard:
        l=self._runtime._latest_plan;s=l.strategy if l else {}
        return StrategyCard(approach=s.get("approach","none"),urgency=s.get("urgency","none"),
            requires_approval=s.get("requires_approval",False),timestamp=datetime.now().timestamp())

    def get_constraints_card(self)->ConstraintsCard:
        l=self._runtime._latest_plan;c=l.constraints if l else {}
        return ConstraintsCard(blocked=c.get("blocked",False),total=c.get("total_constraints",0),
            blocked_count=c.get("blocked_count",0),timestamp=datetime.now().timestamp())

    def get_planning_status_card(self)->PlanningStatusCard:
        l=self._runtime._latest_plan
        return PlanningStatusCard(plan_count=self._runtime._plan_count,has_latest=l is not None,
            latest_ready=l.recommended.readiness if l and l.recommended else "none",timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        l=self._runtime._latest_plan;ta=len(l.alternatives) if l else 0
        return StatisticsCard(total=self._runtime._plan_count,total_alternatives=ta,timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"decision_plan":self.get_decision_plan_card().to_dict(),"alternatives":self.get_alternatives_card().to_dict(),
                "strategy":self.get_strategy_card().to_dict(),"constraints":self.get_constraints_card().to_dict(),
                "planning_status":self.get_planning_status_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
