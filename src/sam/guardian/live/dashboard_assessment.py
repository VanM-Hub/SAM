"""
Guardian Live Dashboard Assessment Bridge.

Provides 6 immutable dashboard cards for operational assessment.
All DTOs are frozen. No async, no threading, no network.
"""

from typing import Dict, Any, List, Optional, TYPE_CHECKING
from dataclasses import dataclass
from datetime import datetime
from collections import defaultdict

from .assessment import GuardianAssessment, AssessmentLevel, RiskLevel, PriorityLevel

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


@dataclass(frozen=True)
class AssessmentOverviewCard:
    total: int; latest_level: Optional[str]; latest_risk: Optional[str]
    latest_priority: Optional[str]; latest_confidence: float; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Assessment Overview","total":self.total,"latest_level":self.latest_level,
                "latest_risk":self.latest_risk,"latest_priority":self.latest_priority,
                "latest_confidence":self.latest_confidence,"timestamp":self.timestamp}

@dataclass(frozen=True)
class RiskMatrixCard:
    risk_counts: Dict[str,int]; highest_risk: str; total: int; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Risk Matrix","risk_counts":dict(self.risk_counts),
                "highest_risk":self.highest_risk,"total":self.total,"timestamp":self.timestamp}

@dataclass(frozen=True)
class PriorityMatrixCard:
    priority_counts: Dict[str,int]; highest_priority: str; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Priority Matrix","priority_counts":dict(self.priority_counts),
                "highest_priority":self.highest_priority,"timestamp":self.timestamp}

@dataclass(frozen=True)
class ConfidenceCard:
    avg_confidence: float; last_confidence: float; total: int; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Confidence","average_confidence":self.avg_confidence,
                "last_confidence":self.last_confidence,"total":self.total,"timestamp":self.timestamp}

@dataclass(frozen=True)
class RuntimeRiskCard:
    total: int; runtime_risks: Dict[str,str]; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Runtime Risk","total":self.total,
                "runtime_risks":dict(self.runtime_risks),"timestamp":self.timestamp}

@dataclass(frozen=True)
class AssessmentHistoryCard:
    total: int; by_level: Dict[str,int]; by_priority: Dict[str,int]; timestamp: float
    def to_dict(self) -> Dict[str,Any]:
        return {"card":"Assessment History","total":self.total,"by_level":dict(self.by_level),
                "by_priority":dict(self.by_priority),"timestamp":self.timestamp}


class LiveDashboardAssessmentBridge:
    """6 immutable cards for assessment dashboard."""

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def card_count(self) -> int:
        return 6

    def get_assessment_overview_card(self) -> AssessmentOverviewCard:
        hist = self._runtime.assessment_history
        latest = hist[-1] if hist else None
        return AssessmentOverviewCard(
            total=len(hist),
            latest_level=latest.level.name if latest else None,
            latest_risk=latest.risk.name if latest else None,
            latest_priority=latest.priority.name if latest else None,
            latest_confidence=latest.confidence if latest else 0.0,
            timestamp=datetime.now().timestamp(),
        )

    def get_risk_matrix_card(self) -> RiskMatrixCard:
        hist = self._runtime.assessment_history
        counts: Dict[str,int] = defaultdict(int)
        highest = "NONE"
        for a in hist:
            counts[a.risk.name] = counts.get(a.risk.name, 0) + 1
            if a.risk.value > RiskLevel[highest].value if highest != "NONE" else 0:
                highest = a.risk.name
        return RiskMatrixCard(risk_counts=dict(counts),highest_risk=highest,total=len(hist),timestamp=datetime.now().timestamp())

    def get_priority_matrix_card(self) -> PriorityMatrixCard:
        hist = self._runtime.assessment_history
        counts: Dict[str,int] = defaultdict(int)
        highest = "LOW"
        for a in hist:
            counts[a.priority.name] = counts.get(a.priority.name, 0) + 1
        return PriorityMatrixCard(priority_counts=dict(counts),highest_priority=highest,timestamp=datetime.now().timestamp())

    def get_confidence_card(self) -> ConfidenceCard:
        hist = self._runtime.assessment_history
        if not hist:
            return ConfidenceCard(avg_confidence=0.0,last_confidence=0.0,total=0,timestamp=datetime.now().timestamp())
        avg = sum(a.confidence for a in hist) / len(hist)
        return ConfidenceCard(avg_confidence=round(avg,2),last_confidence=hist[-1].confidence,total=len(hist),timestamp=datetime.now().timestamp())

    def get_runtime_risk_card(self) -> RuntimeRiskCard:
        hist = self._runtime.assessment_history
        risks: Dict[str,str] = {}
        for a in hist:
            for rid in a.affected_runtimes:
                risks[rid] = a.risk.name
        return RuntimeRiskCard(total=len(risks),runtime_risks=risks,timestamp=datetime.now().timestamp())

    def get_assessment_history_card(self) -> AssessmentHistoryCard:
        hist = self._runtime.assessment_history
        by_level: Dict[str,int] = defaultdict(int)
        by_priority: Dict[str,int] = defaultdict(int)
        for a in hist:
            by_level[a.level.name] += 1
            by_priority[a.priority.name] += 1
        return AssessmentHistoryCard(
            total=len(hist),by_level=dict(by_level),by_priority=dict(by_priority),timestamp=datetime.now().timestamp()
        )

    def get_all_cards(self) -> Dict[str,Any]:
        return {
            "assessment_overview": self.get_assessment_overview_card().to_dict(),
            "risk_matrix": self.get_risk_matrix_card().to_dict(),
            "priority_matrix": self.get_priority_matrix_card().to_dict(),
            "confidence": self.get_confidence_card().to_dict(),
            "runtime_risk": self.get_runtime_risk_card().to_dict(),
            "assessment_history": self.get_assessment_history_card().to_dict(),
        }
