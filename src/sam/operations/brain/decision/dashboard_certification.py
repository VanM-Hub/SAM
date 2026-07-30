"""
Decision Runtime Dashboard Certification Bridge.

6 immutable cards for readiness certification.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3
from .approval_certification import CertificationStatistics

@dataclass(frozen=True)
class CertificationCard:
    has_certification:bool; certification_id:str; activation_id:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Certification","has_certification":self.has_certification,"certification_id":self.certification_id,"activation_id":self.activation_id,"timestamp":self.timestamp}
@dataclass(frozen=True)
class ReadinessCard:
    score:float; certified:bool; state:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Readiness","score":self.score,"certified":self.certified,"state":self.state,"timestamp":self.timestamp}
@dataclass(frozen=True)
class RequirementsCard:
    total:int; met:int; failed:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Requirements","total":self.total,"met":self.met,"failed":self.failed,"timestamp":self.timestamp}
@dataclass(frozen=True)
class EvidenceCard:
    total_evidence:int; total_blockers:int; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Evidence","total_evidence":self.total_evidence,"total_blockers":self.total_blockers,"score":self.score,"timestamp":self.timestamp}
@dataclass(frozen=True)
class HistoryCard:
    total:int; last_event:str; last_state:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"History","total":self.total,"last_event":self.last_event,"last_state":self.last_state,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StatisticsCard:
    total:int; certified:int; blocked:int; failed:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"certified":self.certified,"blocked":self.blocked,"failed":self.failed,"timestamp":self.timestamp}

class DecisionDashboardCertificationBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_certification_card(self)->CertificationCard:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        return CertificationCard(has_certification=c is not None,certification_id=c.certification_id if c else "",activation_id=c.activation_id if c else "",timestamp=datetime.now().timestamp())

    def get_readiness_card(self)->ReadinessCard:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        return ReadinessCard(score=c.readiness_score if c else 0.0,certified=c.certified if c else False,state=c.state.name if c else "NONE",timestamp=datetime.now().timestamp())

    def get_requirements_card(self)->RequirementsCard:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        reqs=c.requirements if c else []
        return RequirementsCard(total=len(reqs),met=sum(1 for r in reqs if r.met),failed=sum(1 for r in reqs if r.required and not r.met),timestamp=datetime.now().timestamp())

    def get_evidence_card(self)->EvidenceCard:
        c=self._runtime._certification_engine.latest if self._runtime._certification_engine else None
        return EvidenceCard(total_evidence=c.evidence_count if c else 0,total_blockers=c.blocker_count if c else 0,score=c.readiness_score if c else 0.0,timestamp=datetime.now().timestamp())

    def get_history_card(self)->HistoryCard:
        h=self._runtime._certification_engine.history if self._runtime._certification_engine else None
        l=h.latest if h else None
        return HistoryCard(total=h.count if h else 0,last_event=l.event if l else "none",last_state=l.state if l else "NONE",timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        s=self._runtime._certification_engine.get_statistics() if self._runtime._certification_engine else CertificationStatistics()
        return StatisticsCard(total=s.total,certified=s.certified,blocked=s.blocked,failed=s.failed,timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"certification":self.get_certification_card().to_dict(),"readiness":self.get_readiness_card().to_dict(),
                "requirements":self.get_requirements_card().to_dict(),"evidence":self.get_evidence_card().to_dict(),
                "history":self.get_history_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
