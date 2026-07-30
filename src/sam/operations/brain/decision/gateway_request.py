"""
Gateway Request DTOs.

DTO for the single official path to Approval Runtime.
Does NOT submit. Preview only.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class GatewayReference:
    submission_plan_id: str = ""; envelope_id: str = ""
    plan_id: str = ""; evaluation_id: str = ""
    def to_dict(self) -> Dict[str,Any]: return {"submission_plan_id":self.submission_plan_id,"envelope_id":self.envelope_id,
        "plan_id":self.plan_id,"evaluation_id":self.evaluation_id}

@dataclass(frozen=True)
class GatewayMetadata:
    gateway_id: str = ""; timestamp: float = 0.0
    source_component: str = "DecisionRuntime"; version: str = "1.0"
    target_component: str = "ApprovalRuntime"
    def to_dict(self) -> Dict[str,Any]: return {"gateway_id":self.gateway_id,"timestamp":self.timestamp,
        "source_component":self.source_component,"version":self.version,"target_component":self.target_component}

@dataclass(frozen=True)
class ApprovalGatewayRequest:
    request_id: str = ""; timestamp: float = 0.0
    references: Optional[GatewayReference] = None
    metadata: Optional[GatewayMetadata] = None
    payload: Optional[Dict[str, Any]] = None
    route: str = "default"; ready: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"request_id":self.request_id,"timestamp":self.timestamp,
        "references":self.references.to_dict() if self.references else None,
        "metadata":self.metadata.to_dict() if self.metadata else None,
        "payload":self.payload,"route":self.route,"ready":self.ready}

@dataclass(frozen=True)
class GatewayStatistics:
    total: int = 0; ready_count: int = 0; blocked_count: int = 0; timestamp: float = 0.0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"ready":self.ready,"blocked":self.blocked,"timestamp":self.timestamp}

@dataclass(frozen=True)
class GatewaySnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    requests: List[ApprovalGatewayRequest] = field(default_factory=list)
    statistics: Optional[GatewayStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "requests":[r.to_dict() for r in self.requests],"statistics":self.statistics.to_dict() if self.statistics else None}
