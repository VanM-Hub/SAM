"""
Decision Planning Runtime DTOs.

Immutable DTOs for decision planning.
Rule-based. No AI. No execution.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


@dataclass(frozen=True)
class DecisionAlternative:
    alternative_id: str = ""
    description: str = ""
    readiness: str = ""
    priority: int = 0
    confidence: float = 0.0
    runtime_ids: List[str] = field(default_factory=list)
    action_type: str = ""
    risks: List[str] = field(default_factory=list)
    score: float = 0.0
    def to_dict(self) -> Dict[str,Any]:
        return {"alternative_id":self.alternative_id,"description":self.description,"readiness":self.readiness,
                "priority":self.priority,"confidence":self.confidence,"runtime_ids":list(self.runtime_ids),
                "action_type":self.action_type,"risks":list(self.risks),"score":self.score}

@dataclass(frozen=True)
class PlanningStage:
    name: str = ""; status: str = ""; result: Optional[Dict[str,Any]] = None
    def to_dict(self) -> Dict[str,Any]: return {"name":self.name,"status":self.status,"result":self.result}

@dataclass(frozen=True)
class DecisionPlan:
    plan_id: str = ""; timestamp: float = 0.0; evaluation_id: str = ""
    alternatives: List[DecisionAlternative] = field(default_factory=list)
    recommended: Optional[DecisionAlternative] = None
    strategy: Optional[Dict[str,Any]] = None
    constraints: Optional[Dict[str,Any]] = None
    stages: List[PlanningStage] = field(default_factory=list)
    summary: str = ""
    def to_dict(self) -> Dict[str,Any]:
        return {"plan_id":self.plan_id,"timestamp":self.timestamp,"evaluation_id":self.evaluation_id,
                "alternatives":[a.to_dict() for a in self.alternatives],
                "recommended":self.recommended.to_dict() if self.recommended else None,
                "strategy":self.strategy,"constraints":self.constraints,
                "stages":[s.to_dict() for s in self.stages],"summary":self.summary}

@dataclass(frozen=True)
class PlanningSummary:
    total: int = 0; ready_count: int = 0; blocked_count: int = 0
    latest_plan: Optional[DecisionPlan] = None
    def to_dict(self) -> Dict[str,Any]:
        return {"total":self.total,"ready":self.ready_count,"blocked":self.blocked_count,
                "latest":self.latest_plan.to_dict() if self.latest_plan else None}

@dataclass(frozen=True)
class PlanningStatistics:
    total: int = 0; total_alternatives: int = 0; avg_confidence: float = 0.0; timestamp: float = 0.0
    def to_dict(self) -> Dict[str,Any]:
        return {"total":self.total,"total_alternatives":self.total_alternatives,"avg_confidence":self.avg_confidence,"timestamp":self.timestamp}

@dataclass(frozen=True)
class PlanningSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    plans: List[DecisionPlan] = field(default_factory=list)
    summary: Optional[PlanningSummary] = None; statistics: Optional[PlanningStatistics] = None
    def to_dict(self) -> Dict[str,Any]:
        return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,"plans":[p.to_dict() for p in self.plans],
                "summary":self.summary.to_dict() if self.summary else None,"statistics":self.statistics.to_dict() if self.statistics else None}
