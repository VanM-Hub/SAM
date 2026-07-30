"""Multi-Level Builder."""
from typing import List
from .multilevel import ApprovalLevel, MultiLevelApproval
from .multilevel_engine import MultiLevelEngine

class MultiLevelBuilder:
    @staticmethod
    def build_default(approval_id:str, workflow_id:str, engine:MultiLevelEngine) -> MultiLevelApproval:
        levels = [
            ApprovalLevel(level_id="L1", name="Team Lead", order=0, required_approvers=1, approvers=["lead"]),
            ApprovalLevel(level_id="L2", name="Manager", order=1, required_approvers=1, approvers=["manager"]),
            ApprovalLevel(level_id="L3", name="Director", order=2, required_approvers=1, approvers=["director"]),
        ]
        return engine.create(approval_id, workflow_id, levels)
