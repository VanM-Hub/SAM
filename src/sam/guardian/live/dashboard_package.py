"""
Guardian Live Dashboard Package Bridge.

6 immutable dashboard cards for decision package.
"""

from typing import Dict,Any,List,TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime

@dataclass(frozen=True)
class DecisionPackageCard:
    package_id:str; version:str; sections:int; has_input:bool; has_just:bool; timestamp:float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Decision Package","package_id":self.package_id,"version":self.version,"sections":self.sections,"has_input":self.has_input,"has_justification":self.has_just,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ValidationCard:
    valid:bool; score:float; errors:int; warnings:int; timestamp:float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Validation","valid":self.valid,"score":self.score,"errors":self.errors,"warnings":self.warnings,"timestamp":self.timestamp}

@dataclass(frozen=True)
class CoverageCard:
    section_names:List[str]; total:int; timestamp:float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Coverage","section_names":list(self.section_names),"total":self.total,"timestamp":self.timestamp}

@dataclass(frozen=True)
class MetadataCard:
    package_id:str; version:str; created_at:float; runtime_id:str; timestamp:float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Metadata","package_id":self.package_id,"version":self.version,"created_at":self.created_at,"runtime_id":self.runtime_id,"timestamp":self.timestamp}

@dataclass(frozen=True)
class HistoryCard:
    total:int; by_version:Dict[str,int]; avg_sections:float; timestamp:float
    def to_dict(self) -> Dict[str,Any]: return {"card":"History","total":self.total,"by_version":dict(self.by_version),"avg_sections":self.avg_sections,"timestamp":self.timestamp}

@dataclass(frozen=True)
class StatisticsCard:
    total:int; total_sections:int; latest_package_id:str; timestamp:float
    def to_dict(self) -> Dict[str,Any]: return {"card":"Statistics","total":self.total,"total_sections":self.total_sections,"latest_package_id":self.latest_package_id,"timestamp":self.timestamp}


class LiveDashboardPackageBridge:
    def __init__(self,runtime:"GuardianLiveRuntime") -> None:
        self._runtime=runtime
    @property
    def card_count(self) -> int: return 6
    def get_decision_package_card(self) -> DecisionPackageCard:
        l=self._runtime.package_registry.latest
        return DecisionPackageCard(package_id=l.package_id if l else "",version=l.metadata.version if l and l.metadata else "",
            sections=l.total_sections if l else 0,has_input=bool(l.decision_input_id if l else ""),
            has_just=bool(l.justification_id if l else ""),timestamp=datetime.now().timestamp())
    def get_validation_card(self) -> ValidationCard:
        from .package_validator import PackageValidator
        l=self._runtime.package_registry.latest
        if not l: return ValidationCard(valid=True,score=1.0,errors=0,warnings=0,timestamp=datetime.now().timestamp())
        r=PackageValidator().validate(l)
        return ValidationCard(valid=r.valid,score=r.score,errors=len(r.errors),warnings=len(r.warnings),timestamp=datetime.now().timestamp())
    def get_coverage_card(self) -> CoverageCard:
        l=self._runtime.package_registry.latest
        return CoverageCard(section_names=list(l.sections.keys()) if l else [],total=l.total_sections if l else 0,timestamp=datetime.now().timestamp())
    def get_metadata_card(self) -> MetadataCard:
        l=self._runtime.package_registry.latest
        return MetadataCard(package_id=l.package_id if l else "",version=l.metadata.version if l and l.metadata else "",
            created_at=l.metadata.created_at if l and l.metadata else 0.0,runtime_id=l.metadata.runtime_id if l and l.metadata else "",timestamp=datetime.now().timestamp())
    def get_history_card(self) -> HistoryCard:
        s=self._runtime.package_registry.get_statistics()
        return HistoryCard(total=s.total,by_version=s.by_version,avg_sections=s.average_sections,timestamp=datetime.now().timestamp())
    def get_statistics_card(self) -> StatisticsCard:
        r=self._runtime.package_registry; l=r.latest
        return StatisticsCard(total=r.count,total_sections=sum(p.total_sections for p in r.history()),latest_package_id=l.package_id if l else "",timestamp=datetime.now().timestamp())
    def get_all_cards(self) -> Dict[str,Any]:
        return {"decision_package":self.get_decision_package_card().to_dict(),"validation":self.get_validation_card().to_dict(),
                "coverage":self.get_coverage_card().to_dict(),"metadata":self.get_metadata_card().to_dict(),
                "history":self.get_history_card().to_dict(),"statistics":self.get_statistics_card().to_dict()}
