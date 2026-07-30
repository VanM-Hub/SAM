"""Multi-Level Validation."""
from typing import Tuple, List
from .multilevel import MultiLevelApproval

class MultiLevelValidator:
    @staticmethod
    def validate(mla: MultiLevelApproval) -> Tuple[bool, List[str]]:
        errors = []
        if not mla.approval_id: errors.append("Missing approval_id")
        if not mla.workflow_id: errors.append("Missing workflow_id")
        if not mla.levels: errors.append("No levels defined")
        else:
            for i, l in enumerate(mla.levels):
                if not l.level_id: errors.append(f"Level {i}: missing level_id")
                if l.required_approvers < 1: errors.append(f"Level {i}: required_approvers must be >= 1")
            order_ids = [l.order for l in mla.levels]
            if order_ids != sorted(order_ids): errors.append("Levels not in order")
        return (len(errors) == 0, errors)
