"""
Decision Runtime Dashboard Approval Bridge.

6 immutable cards for approval preparation.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

@dataclass(frozen=True)
class ApprovalPackageCard:
    has_package:bool; candidates:int; requirements:int; ready:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Approval Package","has_package":self.has_package,"candidates":self.candidates,"requirements":self.requirements,"ready":self.ready,"timestamp":self.timestamp}

@dataclass(frozen=True)
class RequirementsCard:
    total:int; satisfied:int; missing_count:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Requirements","total":self.total,"satisfied":self.satisfied,"missing":self.missing_count,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ValidationCard:
    valid:bool; errors:int; warnings:int; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Validation","valid":self.valid,"errors":self.errors,"warnings":self.warnings,"score":self.score,"timestamp":self.timestamp}

@dataclass(frozen=True)
class SummaryCard:
    ready:bool; risk:str; confidence:float; strategy:str; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Summary","ready":self.ready,"risk":self.risk,"confidence":self.confidence,"strategy":self.strategy,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ReadinessCard:
    ready:bool; total_count:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Readiness","ready":self.ready,"total_count":self.total_count,"timestamp":self.timestamp}

@dataclass(frozen=True)
class StatisticsCard:
    total:int; ready:int; total_reqs:int; satisfied_reqs:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"ready":self.ready,"total_requirements":self.total_reqs,"satisfied_requirements":self.satisfied_reqs,"timestamp":self.timestamp}


class DecisionDashboardApprovalBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_approval_package_card(self)->ApprovalPackageCard:
        l=self._runtime._latest_approval
        return ApprovalPackageCard(has_package=l is not None,candidates=len(l.candidates) if l else 0,
            requirements=len(l.requirements) if l else 0,ready=l.ready_for_submission if l else False,timestamp=datetime.now().timestamp())

    def get_requirements_card(self)->RequirementsCard:
        l=self._runtime._latest_approval
        return RequirementsCard(total=len(l.requirements) if l else 0,satisfied=sum(1 for r in l.requirements if r.satisfied) if l else 0,
            missing_count=sum(1 for r in l.requirements if not r.satisfied) if l else 0,timestamp=datetime.now().timestamp())

    def get_validation_card(self)->ValidationCard:
        from .approval_validator import ApprovalValidator
        l=self._runtime._latest_approval
        if not l: return ValidationCard(valid=True,errors=0,warnings=0,score=1.0,timestamp=datetime.now().timestamp())
        r=ApprovalValidator().validate(l)
        return ValidationCard(valid=r.valid,errors=len(r.errors),warnings=len(r.warnings),score=r.score,timestamp=datetime.now().timestamp())

    def get_summary_card(self)->SummaryCard:
        from .approval_summary import ApprovalSummaryBuilder
        l=self._runtime._latest_approval
        if not l: return SummaryCard(ready=False,risk="UNKNOWN",confidence=0.0,strategy="none",timestamp=datetime.now().timestamp())
        s=ApprovalSummaryBuilder().build(l); d=s.get("decision",{})
        return SummaryCard(ready=l.ready_for_submission,risk=d.get("risk","UNKNOWN"),confidence=d.get("confidence",0.0),
            strategy=s.get("strategy","none"),timestamp=datetime.now().timestamp())

    def get_readiness_card(self)->ReadinessCard:
        l=self._runtime._latest_approval
        return ReadinessCard(ready=l.ready_for_submission if l else False,total_count=self._runtime._approval_count,timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        l=self._runtime._latest_approval
        tr=len(l.requirements) if l else 0; sr=sum(1 for r in l.requirements if r.satisfied) if l else 0
        return StatisticsCard(total=self._runtime._approval_count,ready=self._runtime._approval_ready_count,total_reqs=tr,satisfied_reqs=sr,timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"approval_package":self.get_approval_package_card().to_dict(),"requirements":self.get_requirements_card().to_dict(),
                "validation":self.get_validation_card().to_dict(),"summary":self.get_summary_card().to_dict(),
                "readiness":self.get_readiness_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
