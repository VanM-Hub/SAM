"""
Multi-Level Approval Engine.
"""

from typing import List, Dict, Any, Optional
from .multilevel import ApprovalLevel, LevelStatus, MultiLevelApproval


class MultiLevelEngine:
    def __init__(self) -> None:
        self._approvals: Dict[str, MultiLevelApproval] = {}

    @property
    def approval_count(self) -> int: return len(self._approvals)

    def create(self, approval_id: str, workflow_id: str, levels: List[ApprovalLevel]) -> MultiLevelApproval:
        mla = MultiLevelApproval(approval_id=approval_id, workflow_id=workflow_id, levels=levels)
        self._approvals[approval_id] = mla
        return mla

    def get(self, approval_id: str) -> Optional[MultiLevelApproval]:
        return self._approvals.get(approval_id)

    def get_status(self, approval_id: str) -> Optional[List[LevelStatus]]:
        mla = self._approvals.get(approval_id)
        if not mla: return None
        return [LevelStatus(level_id=l.level_id, completed=l.order < mla.current_level_index or mla.completed,
                approved=1 if (l.order < mla.current_level_index or mla.completed) else 0,
                rejected=0, total_required=l.required_approvers) for l in mla.levels]

    def current_level(self, approval_id: str) -> Optional[ApprovalLevel]:
        mla = self._approvals.get(approval_id)
        if not mla or mla.completed: return None
        if mla.current_level_index < len(mla.levels):
            return mla.levels[mla.current_level_index]
        return None

    def advance_level(self, approval_id: str) -> MultiLevelApproval:
        mla = self._approvals.get(approval_id)
        if not mla: raise ValueError(f"Approval {approval_id} not found")
        if mla.completed: return mla
        new_index = mla.current_level_index + 1
        done = new_index >= len(mla.levels)
        new_mla = MultiLevelApproval(approval_id=mla.approval_id, workflow_id=mla.workflow_id,
            levels=mla.levels, current_level_index=new_index, completed=done)
        self._approvals[approval_id] = new_mla
        return new_mla
