"""
Decision Runtime Dashboard Activation Bridge.

6 immutable cards for activation preview.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3
from .approval_activation import ActivationStatistics

@dataclass(frozen=True)
class ActivationCard:
    has_activation:bool; activation_id:str; lifecycle_id:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Activation","has_activation":self.has_activation,"activation_id":self.activation_id,"lifecycle_id":self.lifecycle_id,"timestamp":self.timestamp}
@dataclass(frozen=True)
class ReadinessCard:
    score:float; ready:bool; state:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Readiness","score":self.score,"ready":self.ready,"state":self.state,"timestamp":self.timestamp}
@dataclass(frozen=True)
class DecisionCard:
    decision:str; state:str; ready:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Decision","decision":self.decision,"state":self.state,"ready":self.ready,"timestamp":self.timestamp}
@dataclass(frozen=True)
class BlockersCard:
    count:int; blockers:list; has_blockers:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Blockers","count":self.count,"blockers":list(self.blockers),"has_blockers":self.has_blockers,"timestamp":self.timestamp}
@dataclass(frozen=True)
class HistoryCard:
    total:int; last_event:str; last_state:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"History","total":self.total,"last_event":self.last_event,"last_state":self.last_state,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StatisticsCard:
    total:int; ready:int; blocked:int; waiting:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"ready":self.ready,"blocked":self.blocked,"waiting":self.waiting,"timestamp":self.timestamp}

class DecisionDashboardActivationBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_activation_card(self)->ActivationCard:
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        return ActivationCard(has_activation=a is not None,activation_id=a.activation_id if a else "",lifecycle_id=a.lifecycle_id if a else "",timestamp=datetime.now().timestamp())

    def get_readiness_card(self)->ReadinessCard:
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        return ReadinessCard(score=a.readiness_score if a else 0.0,ready=a.ready if a else False,state=a.state.name if a else "NONE",timestamp=datetime.now().timestamp())

    def get_decision_card(self)->DecisionCard:
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        return DecisionCard(decision=a.decision.name if a else "NONE",state=a.state.name if a else "NONE",ready=a.ready if a else False,timestamp=datetime.now().timestamp())

    def get_blockers_card(self)->BlockersCard:
        a=self._runtime._activation_engine.latest if self._runtime._activation_engine else None
        return BlockersCard(count=len(a.blockers) if a else 0,blockers=list(a.blockers) if a else [],has_blockers=bool(a.blockers) if a else False,timestamp=datetime.now().timestamp())

    def get_history_card(self)->HistoryCard:
        h=self._runtime._activation_engine.history if self._runtime._activation_engine else None
        l=h.latest if h else None
        return HistoryCard(total=h.count if h else 0,last_event=l.event if l else "none",last_state=l.state if l else "NONE",timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        s=self._runtime._activation_engine.get_statistics() if self._runtime._activation_engine else ActivationStatistics()
        return StatisticsCard(total=s.total,ready=s.ready,blocked=s.blocked,waiting=s.waiting,timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"activation":self.get_activation_card().to_dict(),"readiness":self.get_readiness_card().to_dict(),
                "decision":self.get_decision_card().to_dict(),"blockers":self.get_blockers_card().to_dict(),
                "history":self.get_history_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
