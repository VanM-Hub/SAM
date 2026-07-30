"""
Approval Certification DTOs.

Immutable readiness certification for Approval Runtime pipeline.
Does NOT execute approval. Preview only.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from enum import Enum, auto


class CertificationState(Enum):
    UNKNOWN = auto(); CERTIFIED = auto()
    CONDITIONALLY_READY = auto(); BLOCKED = auto(); FAILED = auto()


class CertificationDecision(Enum):
    APPROVE = auto(); CONDITIONAL = auto(); REJECT = auto(); PENDING = auto()


@dataclass(frozen=True)
class CertificationRequirement:
    name: str = ""; met: bool = False; required: bool = True
    description: str = ""; evidence: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"name":self.name,"met":self.met,"required":self.required,
        "description":self.description,"evidence":self.evidence}

@dataclass(frozen=True)
class ApprovalCertification:
    certification_id: str = ""; activation_id: str = ""; lifecycle_id: str = ""
    timestamp: float = 0.0
    state: CertificationState = CertificationState.UNKNOWN
    decision: CertificationDecision = CertificationDecision.PENDING
    requirements: List[CertificationRequirement] = field(default_factory=list)
    readiness_score: float = 0.0; certified: bool = False
    evidence_count: int = 0; blocker_count: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"certification_id":self.certification_id,"activation_id":self.activation_id,
        "lifecycle_id":self.lifecycle_id,"timestamp":self.timestamp,"state":self.state.name,
        "decision":self.decision.name,"requirements":[r.to_dict() for r in self.requirements],
        "readiness_score":self.readiness_score,"certified":self.certified,
        "evidence_count":self.evidence_count,"blocker_count":self.blocker_count}

@dataclass(frozen=True)
class CertificationStatistics:
    total: int = 0; unknown: int = 0; certified: int = 0
    conditionally_ready: int = 0; blocked: int = 0; failed: int = 0
    approved: int = 0; conditional: int = 0; rejected: int = 0; pending: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"unknown":self.unknown,"certified":self.certified,
        "conditionally_ready":self.conditionally_ready,"blocked":self.blocked,"failed":self.failed,
        "approved":self.approved,"conditional":self.conditional,"rejected":self.rejected,"pending":self.pending}

@dataclass(frozen=True)
class CertificationSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    certifications: List[ApprovalCertification] = field(default_factory=list)
    statistics: Optional[CertificationStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "certifications":[c.to_dict() for c in self.certifications],
        "statistics":self.statistics.to_dict() if self.statistics else None}
