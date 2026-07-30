"""
Decision Runtime Dashboard Submission Bridge.

6 immutable cards for submission orchestration.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
if TYPE_CHECKING: from .runtime_v3 import DecisionRuntimeV3

@dataclass(frozen=True)
class SubmissionPlanCard:
    has_plan:bool; ready:bool; stages:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Submission Plan","has_plan":self.has_plan,"ready":self.ready,"stages":self.stages,"timestamp":self.timestamp}
@dataclass(frozen=True)
class SubmissionQueueCard:
    total:int; urgent:int; normal:int; low:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Submission Queue","total":self.total,"urgent":self.urgent,"normal":self.normal,"low":self.low,"timestamp":self.timestamp}
@dataclass(frozen=True)
class ValidationCard:
    valid:bool; errors:int; warnings:int; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Validation","valid":self.valid,"errors":self.errors,"warnings":self.warnings,"score":self.score,"timestamp":self.timestamp}
@dataclass(frozen=True)
class DependenciesCard:
    total:int; items:list; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Dependencies","total":self.total,"items":list(self.items),"timestamp":self.timestamp}
@dataclass(frozen=True)
class ReadinessCard:
    ready:bool; total_plans:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Readiness","ready":self.ready,"total_plans":self.total_plans,"timestamp":self.timestamp}
@dataclass(frozen=True)
class StatisticsCard:
    total:int; ready:int; blocked:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"ready":self.ready,"blocked":self.blocked,"timestamp":self.timestamp}

class DecisionDashboardSubmissionBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None: self._runtime=runtime
    @property
    def card_count(self)->int: return 6
    def get_submission_plan_card(self)->SubmissionPlanCard:
        l=self._runtime._latest_submission
        return SubmissionPlanCard(has_plan=l is not None,ready=l.ready if l else False,stages=len(l.stages) if l else 0,timestamp=datetime.now().timestamp())
    def get_submission_queue_card(self)->SubmissionQueueCard:
        q=self._runtime._submission_queue
        g=q.priority_groups if q else {}
        return SubmissionQueueCard(total=q.total if q else 0,urgent=len(g.get("urgent",[])) if g else 0,normal=len(g.get("normal",[])) if g else 0,low=len(g.get("low",[])) if g else 0,timestamp=datetime.now().timestamp())
    def get_validation_card(self)->ValidationCard:
        from .submission_validator import SubmissionValidator
        l=self._runtime._latest_submission
        if not l: return ValidationCard(valid=True,errors=0,warnings=0,score=1.0,timestamp=datetime.now().timestamp())
        r=SubmissionValidator().validate(l); return ValidationCard(valid=r.valid,errors=len(r.errors),warnings=len(r.warnings),score=r.score,timestamp=datetime.now().timestamp())
    def get_dependencies_card(self)->DependenciesCard:
        l=self._runtime._latest_submission; d=l.metadata.depends_on if l and l.metadata else []
        return DependenciesCard(total=len(d),items=d,timestamp=datetime.now().timestamp())
    def get_readiness_card(self)->ReadinessCard:
        l=self._runtime._latest_submission
        return ReadinessCard(ready=l.ready if l else False,total_plans=self._runtime._submission_count,timestamp=datetime.now().timestamp())
    def get_statistics_card(self)->StatisticsCard:
        l=self._runtime._latest_submission
        return StatisticsCard(total=self._runtime._submission_count,ready=self._runtime._submission_ready_count,blocked=self._runtime._submission_count-self._runtime._submission_ready_count,timestamp=datetime.now().timestamp())
    def get_all_cards(self)->Dict[str,Any]:
        return {"submission_plan":self.get_submission_plan_card().to_dict(),"submission_queue":self.get_submission_queue_card().to_dict(),
                "validation":self.get_validation_card().to_dict(),"dependencies":self.get_dependencies_card().to_dict(),
                "readiness":self.get_readiness_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
