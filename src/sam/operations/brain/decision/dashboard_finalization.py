"""
Decision Runtime Dashboard Finalization Bridge.

6 immutable cards for final decision record.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3
from .finalization import FinalDecisionStatistics

@dataclass(frozen=True)
class FinalRecordCard:
    has_record:bool; record_id:str; state:str; complete:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"FinalRecord","has_record":self.has_record,"record_id":self.record_id,"state":self.state,"complete":self.complete,"timestamp":self.timestamp}
@dataclass(frozen=True)
class IntegrityCard:
    score:float; state:str; complete:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Integrity","score":self.score,"state":self.state,"complete":self.complete,"timestamp":self.timestamp}
@dataclass(frozen=True)
class CompletionCard:
    complete:bool; stages:int; checks_passed:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Completion","complete":self.complete,"stages":self.stages,"checks_passed":self.checks_passed,"timestamp":self.timestamp}
@dataclass(frozen=True)
class SummaryCard:
    readiness_score:float; cert_state:str; evidence:int; blockers:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Summary","readiness_score":self.readiness_score,"cert_state":self.cert_state,"evidence":self.evidence,"blockers":self.blockers,"timestamp":self.timestamp}
@dataclass(frozen=True)
class HistoryCard:
    total:int; last_event:str; last_state:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"History","total":self.total,"last_event":self.last_event,"last_state":self.last_state,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StatisticsCard:
    total:int; finalized:int; completed:int; archived:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"finalized":self.finalized,"completed":self.completed,"archived":self.archived,"timestamp":self.timestamp}

class DecisionDashboardFinalizationBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_final_record_card(self)->FinalRecordCard:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        return FinalRecordCard(has_record=f is not None,record_id=f.record_id if f else "",state=f.state.name if f else "NONE",complete=f.complete if f else False,timestamp=datetime.now().timestamp())

    def get_integrity_card(self)->IntegrityCard:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        return IntegrityCard(score=f.pipeline_integrity if f else 0.0,state=f.state.name if f else "NONE",complete=f.complete if f else False,timestamp=datetime.now().timestamp())

    def get_completion_card(self)->CompletionCard:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        s=f.summary if f else None
        return CompletionCard(complete=f.complete if f else False,stages=s.pipeline_stages if s else 0,checks_passed=s.checks_passed if s else 0,timestamp=datetime.now().timestamp())

    def get_summary_card(self)->SummaryCard:
        f=self._runtime._finalization_engine.latest if self._runtime._finalization_engine else None
        s=f.summary if f else None
        return SummaryCard(readiness_score=s.readiness_score if s else 0.0,cert_state=s.certification_state if s else "NONE",evidence=s.evidence_count if s else 0,blockers=s.blocker_count if s else 0,timestamp=datetime.now().timestamp())

    def get_history_card(self)->HistoryCard:
        h=self._runtime._finalization_engine.history if self._runtime._finalization_engine else None
        l=h.latest if h else None
        return HistoryCard(total=h.count if h else 0,last_event=l.event if l else "none",last_state=l.state if l else "NONE",timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        s=self._runtime._finalization_engine.get_statistics() if self._runtime._finalization_engine else FinalDecisionStatistics()
        return StatisticsCard(total=s.total,finalized=s.finalized,completed=s.completed,archived=s.archived,timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"record":self.get_final_record_card().to_dict(),"integrity":self.get_integrity_card().to_dict(),
                "completion":self.get_completion_card().to_dict(),"summary":self.get_summary_card().to_dict(),
                "history":self.get_history_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
