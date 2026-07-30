"""
Decision Runtime Dashboard Package Bridge.

6 immutable cards for package consumption.
"""

from typing import Dict,Any,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from .runtime_v3 import DecisionRuntimeV3

@dataclass(frozen=True)
class PackageStatusCard:
    has_package:bool; total_sections:int; has_input:bool; has_just:bool; ready:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Package Status","has_package":self.has_package,
        "total_sections":self.total_sections,"has_input":self.has_input,"has_justification":self.has_just,"ready":self.ready,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ValidationCard:
    valid:bool; errors:int; warnings:int; score:float; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Validation","valid":self.valid,"errors":self.errors,"warnings":self.warnings,"score":self.score,"timestamp":self.timestamp}

@dataclass(frozen=True)
class NormalizationCard:
    normalized:bool; version:str; sections:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Normalization","normalized":self.normalized,"version":self.version,"sections":self.sections,"timestamp":self.timestamp}

@dataclass(frozen=True)
class DecisionContextCard:
    has_context:bool; priority:int; confidence:float; action:str; runtimes:int; ready:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Decision Context","has_context":self.has_context,"priority":self.priority,
        "confidence":self.confidence,"action_type":self.action,"runtimes":self.runtimes,"ready":self.ready,"timestamp":self.timestamp}

@dataclass(frozen=True)
class StatisticsCard:
    total:int; valid:int; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Statistics","total":self.total,"valid":self.valid,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ReadinessCard:
    ready:bool; package_count:int; has_context:bool; validated:bool; timestamp:float
    def to_dict(self)->Dict[str,Any]: return {"card":"Readiness","ready":self.ready,"package_count":self.package_count,"has_context":self.has_context,"validated":self.validated,"timestamp":self.timestamp}


class DecisionDashboardPackageBridge:
    def __init__(self,runtime:"DecisionRuntimeV3")->None:
        self._runtime=runtime
    @property
    def card_count(self)->int: return 6

    def get_package_status_card(self)->PackageStatusCard:
        l=self._runtime._latest_incoming
        return PackageStatusCard(has_package=l is not None,total_sections=l.header.total_sections if l and l.header else 0,
            has_input=l.header.has_input if l and l.header else False,has_just=l.header.has_justification if l and l.header else False,
            ready=l.ready if l else False,timestamp=datetime.now().timestamp())

    def get_validation_card(self)->ValidationCard:
        l=self._runtime._latest_validation
        return ValidationCard(valid=l.valid if l else True,errors=len(l.errors) if l else 0,
            warnings=len(l.warnings) if l else 0,score=l.score if l else 1.0,timestamp=datetime.now().timestamp())

    def get_normalization_card(self)->NormalizationCard:
        l=self._runtime._latest_normalized
        return NormalizationCard(normalized=l is not None,version=l.header.version if l and l.header else "",
            sections=l.header.total_sections if l and l.header else 0,timestamp=datetime.now().timestamp())

    def get_decision_context_card(self)->DecisionContextCard:
        l=self._runtime._latest_context
        return DecisionContextCard(has_context=l is not None,priority=l.priority if l else 0,
            confidence=l.confidence if l else 0.0,action=l.action_type if l else "",runtimes=len(l.runtime_ids) if l else 0,
            ready=l.is_ready if l else False,timestamp=datetime.now().timestamp())

    def get_statistics_card(self)->StatisticsCard:
        return StatisticsCard(total=self._runtime._consume_count,valid=self._runtime._valid_count,timestamp=datetime.now().timestamp())

    def get_readiness_card(self)->ReadinessCard:
        l=self._runtime._latest_context
        return ReadinessCard(ready=l.is_ready if l else False,package_count=self._runtime._consume_count,
            has_context=l is not None,validated=self._runtime._valid_count>0,timestamp=datetime.now().timestamp())

    def get_all_cards(self)->Dict[str,Any]:
        return {"package_status":self.get_package_status_card().to_dict(),"validation":self.get_validation_card().to_dict(),
                "normalization":self.get_normalization_card().to_dict(),"decision_context":self.get_decision_context_card().to_dict(),
                "statistics":self.get_statistics_card().to_dict(),"readiness":self.get_readiness_card().to_dict()}
