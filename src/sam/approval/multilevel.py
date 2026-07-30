"""
Multi-Level Approval DTOs.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional


@dataclass(frozen=True)
class ApprovalLevel:
    level_id: str = ""
    name: str = ""
    order: int = 0
    required_approvers: int = 1
    approvers: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str,Any]: return {"level_id":self.level_id,"name":self.name,"order":self.order,
        "required":self.required_approvers,"approvers":list(self.approvers)}


@dataclass(frozen=True)
class LevelStatus:
    level_id: str = ""
    completed: bool = False
    approved: int = 0
    rejected: int = 0
    total_required: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"level_id":self.level_id,"completed":self.completed,
        "approved":self.approved,"rejected":self.rejected,"total_required":self.total_required}


@dataclass(frozen=True)
class MultiLevelApproval:
    approval_id: str = ""
    workflow_id: str = ""
    levels: List[ApprovalLevel] = field(default_factory=list)
    current_level_index: int = 0
    completed: bool = False
    def to_dict(self) -> Dict[str,Any]: return {"approval_id":self.approval_id,"workflow_id":self.workflow_id,
        "levels":[l.to_dict() for l in self.levels],"current_level":self.current_level_index,"completed":self.completed}
