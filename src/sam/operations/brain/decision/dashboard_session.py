"""
Decision Runtime Dashboard Session Bridge.

6 immutable cards for approval session.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3
from .approval_session import ApprovalSessionStatistics

@dataclass(frozen=True)
class SessionCard:
    has_session:bool; state:str; ready:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Session","has_session":self.has_session,"state":self.state,"ready":self.ready,"timestamp":self.timestamp}
@dataclass(frozen=True)
class RegistryCard:
    total:int; created:int; validated:int; pending:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Registry","total":self.total,"created":self.created,"validated":self.validated,"pending":self.pending,"timestamp":self.timestamp}
@dataclass(frozen=True)
class ValidationCard:
    valid:bool; errors:int; warnings:int; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Validation","valid":self.valid,"errors":self.errors,"warnings":self.warnings,"score":self.score,"timestamp":self.timestamp}
@dataclass(frozen=True)
class HistoryCard:
    total:int; last_event:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"History","total":self.total,"last_event":self.last_event,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StatisticsCard:
    total:int; completed:int; closed:int; cancelled:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"completed":self.completed,"closed":self.closed,"cancelled":self.cancelled,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StateCard:
    state:str; total_sessions:int; active_count:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"State","state":self.state,"total_sessions":self.total_sessions,"active_count":self.active_count,"timestamp":self.timestamp}

class DecisionDashboardSessionBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6
    def get_session_card(self)->SessionCard:
        l=self._runtime._session_registry.latest if self._runtime._session_registry else None
        return SessionCard(has_session=l is not None,state=l.state.name if l else "NONE",ready=l.ready if l else False,timestamp=datetime.now().timestamp())
    def get_registry_card(self)->RegistryCard:
        r=self._runtime._session_registry; s=r.get_statistics() if r else ApprovalSessionStatistics()
        return RegistryCard(total=s.total,created=s.created,validated=s.validated,pending=s.pending,timestamp=datetime.now().timestamp())
    def get_validation_card(self)->ValidationCard:
        from .session_validator import SessionValidator
        l=self._runtime._session_registry.latest if self._runtime._session_registry else None
        if not l: return ValidationCard(valid=True,errors=0,warnings=0,score=1.0,timestamp=datetime.now().timestamp())
        r=SessionValidator().validate(l); return ValidationCard(valid=r.valid,errors=len(r.errors),warnings=len(r.warnings),score=r.score,timestamp=datetime.now().timestamp())
    def get_history_card(self)->HistoryCard:
        h=self._runtime._session_history; l=h.latest if h else None
        return HistoryCard(total=h.count if h else 0,last_event=l.event if l else "none",timestamp=datetime.now().timestamp())
    def get_statistics_card(self)->StatisticsCard:
        s=self._runtime._session_registry.get_statistics() if self._runtime._session_registry else ApprovalSessionStatistics()
        return StatisticsCard(total=s.total,completed=s.completed,closed=s.closed,cancelled=s.cancelled,timestamp=datetime.now().timestamp())
    def get_state_card(self)->StateCard:
        l=self._runtime._session_registry.latest if self._runtime._session_registry else None
        return StateCard(state=l.state.name if l else "NONE",total_sessions=self._runtime._session_registry.count if self._runtime._session_registry else 0,
            active_count=len(self._runtime._session_registry.search("ACTIVE")) if self._runtime._session_registry else 0,timestamp=datetime.now().timestamp())
    def get_all_cards(self)->Dict[str,Any]:
        return {"session":self.get_session_card().to_dict(),"registry":self.get_registry_card().to_dict(),
                "validation":self.get_validation_card().to_dict(),"history":self.get_history_card().to_dict(),
                "statistics":self.get_statistics_card().to_dict(),"state":self.get_state_card().to_dict()}
