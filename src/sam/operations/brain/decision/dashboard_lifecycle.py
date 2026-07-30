"""
Decision Runtime Dashboard Lifecycle Bridge.

6 immutable cards for approval lifecycle.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3
from .approval_lifecycle import LifecycleStatistics

@dataclass(frozen=True)
class LifecycleCard:
    has_lifecycle:bool; state:str; session_id:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Lifecycle","has_lifecycle":self.has_lifecycle,"state":self.state,"session_id":self.session_id,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StateCard:
    state:str; active:bool; is_final:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"State","state":self.state,"active":self.active,"is_final":self.is_final,"timestamp":self.timestamp}
@dataclass(frozen=True)
class TransitionsCard:
    total:int; last_from:str; last_to:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Transitions","total":self.total,"last_from":self.last_from,"last_to":self.last_to,"timestamp":self.timestamp}
@dataclass(frozen=True)
class HistoryCard:
    total:int; last_event:str; last_timestamp:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"History","total":self.total,"last_event":self.last_event,"last_timestamp":self.last_timestamp,"timestamp":self.timestamp}
@dataclass(frozen=True)
class ValidationCard:
    valid:bool; errors:int; warnings:int; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Validation","valid":self.valid,"errors":self.errors,"warnings":self.warnings,"score":self.score,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StatisticsCard:
    total:int; ready:int; waiting:int; closed:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"ready":self.ready,"waiting":self.waiting,"closed":self.closed,"timestamp":self.timestamp}

class DecisionDashboardLifecycleBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_lifecycle_card(self)->LifecycleCard:
        l=self._runtime._lifecycle_engine.latest if self._runtime._lifecycle_engine else None
        return LifecycleCard(has_lifecycle=l is not None,state=l.state.name if l else "NONE",session_id=l.session_id if l else "",timestamp=datetime.now().timestamp())

    def get_state_card(self)->StateCard:
        from .lifecycle_rules import LifecycleRules
        l=self._runtime._lifecycle_engine.latest if self._runtime._lifecycle_engine else None
        s=l.state if l else None
        return StateCard(state=s.name if s else "NONE",active=LifecycleRules.is_active(s) if s else False,is_final=LifecycleRules.is_final(s) if s else False,timestamp=datetime.now().timestamp())

    def get_transitions_card(self)->TransitionsCard:
        l=self._runtime._lifecycle_engine.latest if self._runtime._lifecycle_engine else None
        ts=l.transitions if l else []
        return TransitionsCard(total=len(ts),last_from=ts[-1].from_state if ts else "NONE",last_to=ts[-1].to_state if ts else "NONE",timestamp=datetime.now().timestamp())

    def get_history_card(self)->HistoryCard:
        h=self._runtime._lifecycle_engine.history if self._runtime._lifecycle_engine else None
        l=h.latest if h else None
        return HistoryCard(total=h.count if h else 0,last_event=l.event if l else "none",last_timestamp=l.timestamp if l else 0.0,timestamp=datetime.now().timestamp())

    def get_validation_card(self)->ValidationCard:
        from .lifecycle_validator import LifecycleValidator
        l=self._runtime._lifecycle_engine.latest if self._runtime._lifecycle_engine else None
        if not l: return ValidationCard(valid=True,errors=0,warnings=0,score=1.0,timestamp=datetime.now().timestamp())
        r=LifecycleValidator().validate(l); return ValidationCard(valid=r.valid,errors=len(r.errors),warnings=len(r.warnings),score=r.score,timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        s=self._runtime._lifecycle_engine.get_statistics() if self._runtime._lifecycle_engine else LifecycleStatistics()
        return StatisticsCard(total=s.total,ready=s.ready,waiting=s.waiting,closed=s.closed,timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"lifecycle":self.get_lifecycle_card().to_dict(),"state":self.get_state_card().to_dict(),
                "transitions":self.get_transitions_card().to_dict(),"history":self.get_history_card().to_dict(),
                "validation":self.get_validation_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
