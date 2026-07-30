"""
Approval Status Mirror.

Read-only mirror of approval state.
Does NOT change approval state.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Any
from datetime import datetime


class ApprovalState:
    PENDING = "PENDING"; APPROVED = "APPROVED"; REJECTED = "REJECTED"
    ESCALATED = "ESCALATED"; EXPIRED = "EXPIRED"


@dataclass(frozen=True)
class ApprovalStatusMirror:
    envelope_id: str = ""; state: str = ApprovalState.PENDING
    timestamp: float = 0.0; message: str = ""
    references: Dict[str, str] = field(default_factory=dict)
    def to_dict(self) -> Dict[str,Any]: return {"envelope_id":self.envelope_id,"state":self.state,
        "timestamp":self.timestamp,"message":self.message,"references":dict(self.references)}

@dataclass(frozen=True)
class ApprovalStateSummary:
    total: int = 0; pending: int = 0; approved: int = 0
    rejected: int = 0; escalated: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"pending":self.pending,
        "approved":self.approved,"rejected":self.rejected,"escalated":self.escalated}

@dataclass(frozen=True)
class ApprovalStateStatistics:
    total: int = 0; by_state: Dict[str,int] = field(default_factory=dict)
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"by_state":dict(self.by_state)}


class ApprovalStatusMirrorStore:
    """Read-only store for approval state mirrors."""

    def __init__(self) -> None:
        self._mirrors: List[ApprovalStatusMirror] = []

    def record(self, mirror: ApprovalStatusMirror) -> None:
        self._mirrors.append(mirror)

    @property
    def latest(self) -> ApprovalStatusMirror:
        return self._mirrors[-1] if self._mirrors else ApprovalStatusMirror()

    def get_summary(self) -> ApprovalStateSummary:
        pending = sum(1 for m in self._mirrors if m.state == ApprovalState.PENDING)
        approved = sum(1 for m in self._mirrors if m.state == ApprovalState.APPROVED)
        rejected = sum(1 for m in self._mirrors if m.state == ApprovalState.REJECTED)
        escalated = sum(1 for m in self._mirrors if m.state == ApprovalState.ESCALATED)
        return ApprovalStateSummary(total=len(self._mirrors),pending=pending,approved=approved,
                                     rejected=rejected,escalated=escalated)
