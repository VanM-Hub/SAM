"""
Guardian Live Conversation Assessment Bridge.

Provides 10 DTO-only query methods for operational assessment.
No async, no threading, no network.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime
from collections import defaultdict

from .assessment import GuardianAssessment, AssessmentLevel, RiskLevel, PriorityLevel

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationAssessmentBridge:
    """10 queries for operational assessment."""

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def query_count(self) -> int:
        return 10

    def latest_assessment(self) -> Dict[str, Any]:
        hist = self._runtime.assessment_history
        latest = hist[-1] if hist else None
        return {
            "query": "latest_assessment",
            "timestamp": datetime.now().timestamp(),
            "has_assessment": latest is not None,
            "assessment": latest.to_dict() if latest else None,
        }

    def current_risk(self) -> Dict[str, Any]:
        hist = self._runtime.assessment_history
        latest = hist[-1] if hist else None
        return {
            "query": "current_risk",
            "risk": latest.risk.name if latest else "NONE",
            "priority": latest.priority.name if latest else "NONE",
            "confidence": latest.confidence if latest else 0.0,
        }

    def priority(self) -> Dict[str, Any]:
        return self.current_risk()

    def confidence(self) -> Dict[str, Any]:
        hist = self._runtime.assessment_history
        if not hist:
            return {"query":"confidence","avg":0.0,"count":0}
        avg = sum(a.confidence for a in hist) / len(hist)
        return {"query":"confidence","average_confidence":round(avg,2),"total":len(hist)}

    def runtime_assessment(self, runtime_id: str) -> Dict[str, Any]:
        hist = self._runtime.assessment_history
        relevant = [a for a in hist if runtime_id in a.affected_runtimes]
        return {
            "query":"runtime_assessment","runtime_id":runtime_id,
            "count":len(relevant),"assessments":[a.to_dict() for a in relevant[-10:]],
        }

    def history(self, limit: int = 50) -> Dict[str, Any]:
        hist = self._runtime.assessment_history
        recent = hist[-limit:] if limit > 0 else hist
        return {
            "query":"history","total":len(hist),"returned":len(recent),
            "assessments":[a.to_dict() for a in recent],
        }

    def statistics(self) -> Dict[str, Any]:
        hist = self._runtime.assessment_history
        by_level = defaultdict(int)
        by_risk = defaultdict(int)
        by_priority = defaultdict(int)
        for a in hist:
            by_level[a.level.name] += 1
            by_risk[a.risk.name] += 1
            by_priority[a.priority.name] += 1
        return {
            "query":"statistics","total":len(hist),
            "by_level":dict(by_level),"by_risk":dict(by_risk),"by_priority":dict(by_priority),
        }

    def critical_assessment(self) -> Dict[str, Any]:
        hist = self._runtime.assessment_history
        critical = [a for a in hist if a.level in (AssessmentLevel.CRITICAL, AssessmentLevel.CONCERN)]
        return {
            "query":"critical_assessment","count":len(critical),
            "assessments":[a.to_dict() for a in critical[-20:]],
        }

    def assessment_summary(self) -> Dict[str, Any]:
        return self.statistics()

    def overall_health(self) -> Dict[str, Any]:
        hist = self._runtime.assessment_history
        if not hist:
            return {"query":"overall_health","status":"UNKNOWN","risk":"NONE","confidence":0.0}
        latest = hist[-1]
        status = "GOOD"
        if latest.risk in (RiskLevel.CRITICAL, RiskLevel.HIGH):
            status = "CRITICAL"
        elif latest.risk == RiskLevel.MEDIUM:
            status = "WARNING"
        return {
            "query":"overall_health","status":status,
            "risk":latest.risk.name,"priority":latest.priority.name,
            "confidence":latest.confidence,"total_assessments":len(hist),
        }
