"""
Decision Evaluation Runtime DTOs.

Immutable DTOs for decision evaluation.
Rule-based. Deterministic. No AI.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any


class ReadinessLevel:
    READY = "READY"; PARTIAL = "PARTIAL"; BLOCKED = "BLOCKED"


class ConfidenceLevel:
    LOW = "LOW"; MEDIUM = "MEDIUM"; HIGH = "HIGH"; VERY_HIGH = "VERY_HIGH"


@dataclass(frozen=True)
class EvaluationReason:
    primary: str = ""; details: List[str] = field(default_factory=list)
    rules_triggered: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str,Any]: return {"primary":self.primary,"details":list(self.details),"rules_triggered":list(self.rules_triggered)}

@dataclass(frozen=True)
class EvaluationResult:
    passed: bool = False; score: float = 0.0
    violations: List[str] = field(default_factory=list); warnings: List[str] = field(default_factory=list)
    def to_dict(self) -> Dict[str,Any]: return {"passed":self.passed,"score":self.score,"violations":list(self.violations),"warnings":list(self.warnings)}

@dataclass(frozen=True)
class DecisionEvaluation:
    evaluation_id: str = ""; timestamp: float = 0.0; context_id: str = ""
    ready: str = ReadinessLevel.PARTIAL; confidence: str = ConfidenceLevel.MEDIUM
    policy_result: Optional[EvaluationResult] = None
    readiness_result: Optional[EvaluationResult] = None
    overall_result: Optional[EvaluationResult] = None
    reasons: List[EvaluationReason] = field(default_factory=list)
    def to_dict(self) -> Dict[str,Any]: return {"evaluation_id":self.evaluation_id,"timestamp":self.timestamp,"context_id":self.context_id,
        "ready":self.ready,"confidence":self.confidence,
        "policy_result":self.policy_result.to_dict() if self.policy_result else None,
        "readiness_result":self.readiness_result.to_dict() if self.readiness_result else None,
        "overall_result":self.overall_result.to_dict() if self.overall_result else None,
        "reasons":[r.to_dict() for r in self.reasons]}

@dataclass(frozen=True)
class EvaluationSummary:
    total: int = 0; ready_count: int = 0; blocked_count: int = 0; partial_count: int = 0
    passed_count: int = 0; period_start: float = 0.0; period_end: float = 0.0
    latest: Optional[DecisionEvaluation] = None
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"ready":self.ready_count,"blocked":self.blocked_count,
        "partial":self.partial_count,"passed":self.passed_count,"period_start":self.period_start,"period_end":self.period_end,
        "latest":self.latest.to_dict() if self.latest else None}

@dataclass(frozen=True)
class EvaluationStatistics:
    total: int = 0; by_readiness: Dict[str,int] = field(default_factory=dict)
    by_confidence: Dict[str,int] = field(default_factory=dict); avg_score: float = 0.0; timestamp: float = 0.0
    def to_dict(self) -> Dict[str,Any]: return {"total":self.total,"by_readiness":dict(self.by_readiness),
        "by_confidence":dict(self.by_confidence),"average_score":self.avg_score,"timestamp":self.timestamp}

@dataclass(frozen=True)
class EvaluationSnapshot:
    snapshot_id: str = ""; timestamp: float = 0.0
    evaluations: List[DecisionEvaluation] = field(default_factory=list)
    summary: Optional[EvaluationSummary] = None; statistics: Optional[EvaluationStatistics] = None
    def to_dict(self) -> Dict[str,Any]: return {"snapshot_id":self.snapshot_id,"timestamp":self.timestamp,
        "evaluations":[e.to_dict() for e in self.evaluations],"summary":self.summary.to_dict() if self.summary else None,
        "statistics":self.statistics.to_dict() if self.statistics else None}
