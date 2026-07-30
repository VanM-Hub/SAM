"""
Guardian Decision Package DTOs.

Immutable package containing all data needed by Decision Runtime.
DTO only. No execution, no missions, no approvals.
"""

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, List, Optional, Any


class PackageVersion(Enum):
    V1_0 = "1.0"

    @classmethod
    def current(cls) -> "PackageVersion":
        return cls.V1_0

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True)
class PackageMetadata:
    package_id: str = ""; version: str = "1.0"
    created_at: float = 0.0; source_component: str = "GuardianLiveRuntime"
    runtime_id: str = ""; description: str = ""
    def to_dict(self) -> Dict[str,Any]:
        return {"package_id":self.package_id,"version":self.version,"created_at":self.created_at,
                "source_component":self.source_component,"runtime_id":self.runtime_id,"description":self.description}

@dataclass(frozen=True)
class DecisionPackage:
    package_id: str = ""; metadata: Optional[PackageMetadata] = None
    sections: Dict[str, Any] = field(default_factory=dict)
    total_sections: int = 0
    decision_input_id: str = ""
    justification_id: str = ""
    def to_dict(self) -> Dict[str,Any]:
        return {"package_id":self.package_id,"metadata":self.metadata.to_dict() if self.metadata else None,
                "sections":{k:v for k,v in self.sections.items()},"total_sections":self.total_sections,
                "decision_input_id":self.decision_input_id,"justification_id":self.justification_id}

@dataclass(frozen=True)
class PackageStatistics:
    total: int = 0; by_version: Dict[str,int] = field(default_factory=dict)
    average_sections: float = 0.0; total_sections: int = 0
    def to_dict(self) -> Dict[str,Any]:
        return {"total":self.total,"by_version":dict(self.by_version),
                "average_sections":self.average_sections,"total_sections":self.total_sections}

@dataclass(frozen=True)
class PackageSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    total_packages: int = 0; packages: List[DecisionPackage] = field(default_factory=list)
    statistics: Optional[PackageStatistics] = None
    def to_dict(self) -> Dict[str,Any]:
        return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,"total_packages":self.total_packages,
                "packages":[p.to_dict() for p in self.packages],"statistics":self.statistics.to_dict() if self.statistics else None}

@dataclass(frozen=True)
class PackageSummary:
    total: int = 0; latest_package_id: str = ""; total_sections: int = 0
    versions: List[str] = field(default_factory=list); latest_timestamp: float = 0.0
    def to_dict(self) -> Dict[str,Any]:
        return {"total":self.total,"latest_package_id":self.latest_package_id,"total_sections":self.total_sections,
                "versions":list(self.versions),"latest_timestamp":self.latest_timestamp}
