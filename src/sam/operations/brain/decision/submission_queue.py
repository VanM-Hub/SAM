"""
Submission Queue Planner.

Plans submission order. Rule-based. No scheduler.
"""

from typing import List, Dict, Any
from dataclasses import dataclass, field


@dataclass(frozen=True)
class SubmissionQueue:
    ordered_ids: List[str] = field(default_factory=list)
    priority_groups: Dict[str, List[str]] = field(default_factory=dict)
    total: int = 0
    def to_dict(self) -> Dict[str,Any]: return {"ordered_ids":list(self.ordered_ids),"priority_groups":{k:list(v) for k,v in self.priority_groups.items()},"total":self.total}


class SubmissionQueuePlanner:
    def plan(self, plans: list) -> SubmissionQueue:
        priority_groups: Dict[str, list] = {"urgent": [], "normal": [], "low": []}
        for p in plans:
            pri = p.metadata.priority if hasattr(p, 'metadata') and p.metadata else 0
            if pri >= 3: priority_groups["urgent"].append(p.plan_id)
            elif pri >= 1: priority_groups["normal"].append(p.plan_id)
            else: priority_groups["low"].append(p.plan_id)
        ordered = priority_groups["urgent"] + priority_groups["normal"] + priority_groups["low"]
        return SubmissionQueue(ordered_ids=ordered, priority_groups=priority_groups, total=len(plans))
