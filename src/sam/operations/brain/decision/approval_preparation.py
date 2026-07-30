"""
Approval Preparation Runtime DTOs.

Immutable DTOs for preparing approval packages.
Does NOT submit approvals. DTO only.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class ApprovalRequirement:
    name: str = ""; category: str = ""; satisfied: bool = False
    details: Optional[Dict[str, Any]] = None
    def to_dict(self) -> Dict[str,Any]: return {"name":self.name,"category":self.category,"satisfied":self.satisfied,"details":self.details}

@dataclass(frozen=True)
class ApprovalCandidate:
    candidate_id: str = ""; runtime_id: str = ""; action_type: str = ""
    priority: int = 0; confidence: float = 0.0; requires_approval: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"candidate_id":self.candidate_id,"runtime_id":self.runtime_id,
        "action_type":self.action_type,"priority":self.priority,"confidence":self.confidence,"requires_approval":self.requires_approval}

@dataclass(frozen=True)
class ApprovalMetadata:
    plan_id: str = ""; evaluation_id: str = ""
    strategy_approach: str = ""; requires_approval: bool = False
    created_at: float = 0.0; version: str = "1.0"
    def to_dict(self) -> Dict[str,Any]: return {"plan_id":self.plan_id,"evaluation_id":self.evaluation_id,
        "strategy_approach":self.strategy_approach,"requires_approval":self.requires_approval,"created_at":self.created_at,"version":self.version}

@dataclass(frozen=True)
class ApprovalPreparation:
    preparation_id: str = ""; timestamp: float = 0.0
    metadata: Optional[ApprovalMetadata] = None
    candidates: List[ApprovalCandidate] = field(default_factory=list)
    requirements: List[ApprovalRequirement] = field(default_factory=list)
    summary: str = ""
    ready_for_submission: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"preparation_id":self.preparation_id,"timestamp":self.timestamp,
        "metadata":self.metadata.to_dict() if self.metadata else None,
        "candidates":[c.to_dict() for c in self.candidates],
        "requirements":[r.to_dict() for r in self.requirements],
        "summary":self.summary,"ready_for_submission":self.ready_for_submission}

@dataclass(frozen=True)
class ApprovalStatistics:
    total: int = 0; ready_count: int = 0; blocked_count: int = 0
    total_requirements: int = 0; satisfied_requirements: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"ready":self.ready_count,"blocked":self.blocked_count,
        "total_requirements":self.total_requirements,"satisfied_requirements":self.satisfied_requirements}

@dataclass(frozen=True)
class ApprovalSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    preparations: List[ApprovalPreparation] = field(default_factory=list)
    statistics: Optional[ApprovalStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "preparations":[p.to_dict() for p in self.preparations],"statistics":self.statistics.to_dict() if self.statistics else None}
