"""
Guardian Live Conversation Transition Bridge.

Provides 10 DTO-only query methods for transition intelligence.
All methods return frozen dicts. No async, no threading, no network.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from .transition import TransitionType, ImpactLevel

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationTransitionBridge:
    """
    Bridge for transition intelligence queries.

    Provides 10 query methods:
        1. latest_transition   - Most recent transition
        2. transition_history  - All transitions in timeline
        3. critical_changes   - Filtered critical/high impact
        4. runtime_changes    - Changes for specific runtime
        5. health_changes     - Health-related transitions
        6. version_changes    - Version-related transitions
        7. timeline           - Full timeline state
        8. impact             - Current impact analysis
        9. statistics         - Transition statistics
        10. summary           - Full transition summary

    All DTO-only.
    """

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def query_count(self) -> int:
        return 10

    def latest_transition(self) -> Dict[str, Any]:
        latest = self._runtime.timeline.latest
        return {
            "query": "latest_transition",
            "timestamp": datetime.now().timestamp(),
            "has_transition": latest is not None,
            "transition": latest.to_dict() if latest else None,
        }

    def transition_history(self, limit: int = 50) -> Dict[str, Any]:
        all_t = self._runtime.timeline.get_all()
        recent = all_t[-limit:] if limit > 0 else all_t
        return {
            "query": "transition_history",
            "timestamp": datetime.now().timestamp(),
            "total": len(all_t),
            "returned": len(recent),
            "transitions": [t.to_dict() for t in recent],
        }

    def critical_changes(self, limit: int = 20) -> Dict[str, Any]:
        critical = self._runtime.timeline.filter(
            min_impact=ImpactLevel.HIGH,
            limit=limit,
        )
        return {
            "query": "critical_changes",
            "timestamp": datetime.now().timestamp(),
            "count": len(critical),
            "transitions": [t.to_dict() for t in critical],
        }

    def runtime_changes(self, runtime_id: str, limit: int = 20) -> Dict[str, Any]:
        filtered = self._runtime.timeline.filter(
            runtime_id=runtime_id,
            limit=limit,
        )
        return {
            "query": "runtime_changes",
            "runtime_id": runtime_id,
            "timestamp": datetime.now().timestamp(),
            "count": len(filtered),
            "transitions": [t.to_dict() for t in filtered],
        }

    def health_changes(self, limit: int = 20) -> Dict[str, Any]:
        health = self._runtime.timeline.filter(
            transition_type=TransitionType.HEALTH_CHANGED,
            limit=limit,
        )
        return {
            "query": "health_changes",
            "timestamp": datetime.now().timestamp(),
            "count": len(health),
            "transitions": [t.to_dict() for t in health],
        }

    def version_changes(self, limit: int = 20) -> Dict[str, Any]:
        versions = self._runtime.timeline.filter(
            transition_type=TransitionType.VERSION_CHANGED,
            limit=limit,
        )
        return {
            "query": "version_changes",
            "timestamp": datetime.now().timestamp(),
            "count": len(versions),
            "transitions": [t.to_dict() for t in versions],
        }

    def timeline(self) -> Dict[str, Any]:
        return {
            "query": "timeline",
            "timestamp": datetime.now().timestamp(),
            "count": self._runtime.timeline.count,
            "summary": self._runtime.timeline.get_summary().to_dict(),
        }

    def impact(self) -> Dict[str, Any]:
        all_t = self._runtime.timeline.get_all()
        impact_result = self._runtime.impact_analyzer.analyze_batch(all_t)
        return {
            "query": "impact",
            "timestamp": datetime.now().timestamp(),
            "analysis": impact_result,
        }

    def statistics(self) -> Dict[str, Any]:
        stats = self._runtime.timeline.get_statistics()
        return {
            "query": "statistics",
            "timestamp": datetime.now().timestamp(),
            "statistics": stats.to_dict(),
        }

    def summary(self) -> Dict[str, Any]:
        summary_obj = self._runtime.timeline.get_summary()
        all_t = self._runtime.timeline.get_all()
        impact_result = self._runtime.impact_analyzer.analyze_batch(all_t)
        return {
            "query": "summary",
            "timestamp": datetime.now().timestamp(),
            "summary": summary_obj.to_dict(),
            "impact": impact_result,
        }
