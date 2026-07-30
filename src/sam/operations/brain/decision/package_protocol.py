"""
Decision Runtime Package Protocol DTOs.

DTO for receiving and processing DecisionPackage from Guardian.
Compatible with Guardian DecisionPackage but independent.
Immutable. No async, no threading, no network.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime


@dataclass(frozen=True)
class PackageHeader:
    source_package_id: str = ""
    source_component: str = ""
    received_at: float = 0.0
    version: str = "1.0"
    total_sections: int = 0
    has_input: bool = False
    has_justification: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"source_package_id":self.source_package_id,"source_component":self.source_component,
                "received_at":self.received_at,"version":self.version,"total_sections":self.total_sections,
                "has_input":self.has_input,"has_justification":self.has_justification}


@dataclass(frozen=True)
class PackageBody:
    sections: Dict[str, Any] = field(default_factory=dict)
    decision_input: Optional[Dict[str, Any]] = None
    justification: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {"sections": dict(self.sections), "decision_input": self.decision_input,
                "justification": self.justification, "metadata": self.metadata}


@dataclass(frozen=True)
class IncomingDecisionPackage:
    package_id: str = ""
    header: Optional[PackageHeader] = None
    body: Optional[PackageBody] = None
    normalized: Optional["IncomingDecisionPackage"] = None
    validation_errors: List[str] = field(default_factory=list)
    ready: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {"package_id":self.package_id,"header":self.header.to_dict() if self.header else None,
                "body":self.body.to_dict() if self.body else None,
                "normalized":self.normalized.to_dict() if self.normalized else None,
                "validation_errors":list(self.validation_errors),"ready":self.ready}
