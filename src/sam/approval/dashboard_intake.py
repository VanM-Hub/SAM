"""
Approval Runtime Dashboard Intake Bridge.

6 immutable cards for intake runtime.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v1 import ApprovalRuntimeV1


@dataclass(frozen=True)
class IntakeCard:
    has_intake:bool; record_id:str; source:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Intake","has_intake":self.has_intake,"record_id":self.record_id,"source":self.source,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ValidationCard:
    valid:bool; errors:int; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Validation","valid":self.valid,"errors":self.errors,"score":self.score,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ReadinessCard:
    readiness:str; score:float; certified:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Readiness","readiness":self.readiness,"score":self.score,"certified":self.certified,"timestamp":self.timestamp}

@dataclass(frozen=True)
class WarningsCard:
    count:int; has_warnings:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Warnings","count":self.count,"has_warnings":self.has_warnings,"timestamp":self.timestamp}

@dataclass(frozen=True)
class RegistryCard:
    count:int; has_latest:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Registry","count":self.count,"has_latest":self.has_latest,"timestamp":self.timestamp}

@dataclass(frozen=True)
class SummaryCard:
    readiness_score:float; findings:int; warnings:int; readiness:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Summary","readiness_score":self.readiness_score,"findings":self.findings,"warnings":self.warnings,"readiness":self.readiness,"timestamp":self.timestamp}


class DashboardIntakeBridge:
    def __init__(self,runtime:"ApprovalRuntimeV1")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_intake_card(self)->IntakeCard:
        l=self._runtime._registry.latest if self._runtime._registry else None
        src=l.metadata.source.name if l and l.metadata else "NONE"
        return IntakeCard(has_intake=l is not None,record_id=l.record_id if l else "",source=src,timestamp=datetime.now().timestamp())

    def get_validation_card(self)->ValidationCard:
        v=self._runtime._last_validation
        return ValidationCard(valid=v.valid if v else True,errors=len(v.errors) if v else 0,score=v.score if v else 1.0,timestamp=datetime.now().timestamp())

    def get_readiness_card(self)->ReadinessCard:
        s=self._runtime._last_summary
        return ReadinessCard(readiness=s.readiness if s else "UNKNOWN",score=s.readiness_score if s else 0.0,certified=s.certified if s else False,timestamp=datetime.now().timestamp())

    def get_warnings_card(self)->WarningsCard:
        v=self._runtime._last_validation
        return WarningsCard(count=len(v.warnings) if v else 0,has_warnings=bool(v.warnings) if v else False,timestamp=datetime.now().timestamp())

    def get_registry_card(self)->RegistryCard:
        r=self._runtime._registry
        return RegistryCard(count=r.count if r else 0,has_latest=r.latest is not None if r else False,timestamp=datetime.now().timestamp())

    def get_summary_card(self)->SummaryCard:
        s=self._runtime._last_summary
        return SummaryCard(readiness_score=s.readiness_score if s else 0.0,findings=s.findings if s else 0,warnings=s.warnings if s else 0,readiness=s.readiness if s else "UNKNOWN",timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"intake":self.get_intake_card().to_dict(),"validation":self.get_validation_card().to_dict(),
                "readiness":self.get_readiness_card().to_dict(),"warnings":self.get_warnings_card().to_dict(),
                "registry":self.get_registry_card().to_dict(),"summary":self.get_summary_card().to_dict()}
