"""
Decision Runtime Dashboard Evaluation Bridge.

6 immutable cards for decision evaluation.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

@dataclass(frozen=True)
class EvaluationCard:
    ready:str; confidence:str; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Evaluation","ready":self.ready,"confidence":self.confidence,"score":self.score,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ReadinessCard:
    ready:str; violations:int; warnings:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Readiness","ready":self.ready,"violations":self.violations,"warnings":self.warnings,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ConfidenceCard:
    level:str; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Confidence","level":self.level,"score":self.score,"timestamp":self.timestamp}

@dataclass(frozen=True)
class PolicyCard:
    passed:bool; violations:int; warnings:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Policy","passed":self.passed,"violations":self.violations,"warnings":self.warnings,"timestamp":self.timestamp}

@dataclass(frozen=True)
class WarningsCard:
    total:int; items:list; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Warnings","total":self.total,"items":list(self.items),"timestamp":self.timestamp}

@dataclass(frozen=True)
class StatisticsCard:
    total:int; ready:int; blocked:int; partial:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"ready":self.ready,"blocked":self.blocked,"partial":self.partial,"timestamp":self.timestamp}


class DecisionDashboardEvaluationBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_evaluation_card(self)->EvaluationCard:
        l=self._runtime._latest_evaluation
        return EvaluationCard(ready=l.ready if l else "UNKNOWN",confidence=l.confidence if l else "UNKNOWN",
            score=l.overall_result.score if l and l.overall_result else 0.0,timestamp=datetime.now().timestamp())

    def get_readiness_card(self)->ReadinessCard:
        l=self._runtime._latest_evaluation
        r=l.readiness_result if l else None
        return ReadinessCard(ready=l.ready if l else "UNKNOWN",violations=len(r.violations) if r else 0,warnings=len(r.warnings) if r else 0,timestamp=datetime.now().timestamp())

    def get_confidence_card(self)->ConfidenceCard:
        l=self._runtime._latest_evaluation
        return ConfidenceCard(level=l.confidence if l else "UNKNOWN",score=l.overall_result.score if l and l.overall_result else 0.0,timestamp=datetime.now().timestamp())

    def get_policy_card(self)->PolicyCard:
        l=self._runtime._latest_evaluation;p=l.policy_result if l else None
        return PolicyCard(passed=p.passed if p else True,violations=len(p.violations) if p else 0,warnings=len(p.warnings) if p else 0,timestamp=datetime.now().timestamp())

    def get_warnings_card(self)->WarningsCard:
        l=self._runtime._latest_evaluation;items=[]
        if l:
            if l.readiness_result: items.extend(l.readiness_result.warnings)
            if l.policy_result: items.extend(l.policy_result.warnings)
        return WarningsCard(total=len(items),items=items,timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        return StatisticsCard(total=self._runtime._evaluation_count,ready=self._runtime._ready_count,
            blocked=self._runtime._blocked_count,partial=self._runtime._evaluation_count-self._runtime._ready_count-self._runtime._blocked_count,
            timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"evaluation":self.get_evaluation_card().to_dict(),"readiness":self.get_readiness_card().to_dict(),
                "confidence":self.get_confidence_card().to_dict(),"policy":self.get_policy_card().to_dict(),
                "warnings":self.get_warnings_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
