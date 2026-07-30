"""
Guardian Live Conversation Situation Bridge.

Provides 10 DTO-only query methods for situation intelligence.
No async, no threading, no network.
"""

from typing import Dict, Any, Optional, TYPE_CHECKING
from datetime import datetime

from .situation import SituationType, SituationSeverity

if TYPE_CHECKING:
    from .runtime import GuardianLiveRuntime


class LiveConversationSituationBridge:
    """10 query bridge for situation intelligence."""

    def __init__(self, runtime: "GuardianLiveRuntime") -> None:
        self._runtime = runtime

    @property
    def query_count(self) -> int:
        return 10

    def latest_situation(self) -> Dict[str, Any]:
        latest = self._runtime.situation_history.latest
        return {
            "query": "latest_situation",
            "timestamp": datetime.now().timestamp(),
            "has_situation": latest is not None,
            "situation": latest.to_dict() if latest else None,
        }

    def current_situation(self) -> Dict[str, Any]:
        return self.latest_situation()

    def history(self, limit: int = 50) -> Dict[str, Any]:
        all_s = self._runtime.situation_history.get_all()
        recent = all_s[-limit:] if limit > 0 else all_s
        return {
            "query": "history",
            "timestamp": datetime.now().timestamp(),
            "total": len(all_s),
            "returned": len(recent),
            "situations": [s.to_dict() for s in recent],
        }

    def critical_situations(self, limit: int = 20) -> Dict[str, Any]:
        critical = self._runtime.situation_history.filter(
            min_severity=SituationSeverity.HIGH,
            limit=limit,
        )
        return {
            "query": "critical_situations",
            "timestamp": datetime.now().timestamp(),
            "count": len(critical),
            "situations": [s.to_dict() for s in critical],
        }

    def busy_runtime(self) -> Dict[str, Any]:
        busy = self._runtime.situation_history.filter(
            situation_type=SituationType.BUSY,
            limit=5,
        )
        return {
            "query": "busy_runtime",
            "timestamp": datetime.now().timestamp(),
            "count": len(busy),
            "situations": [s.to_dict() for s in busy],
        }

    def approval_bottleneck(self) -> Dict[str, Any]:
        bottleneck = self._runtime.situation_history.filter(
            situation_type=SituationType.APPROVAL_BOTTLENECK,
            limit=5,
        )
        return {
            "query": "approval_bottleneck",
            "timestamp": datetime.now().timestamp(),
            "count": len(bottleneck),
            "situations": [s.to_dict() for s in bottleneck],
        }

    def recovery(self) -> Dict[str, Any]:
        recovery = self._runtime.situation_history.filter(
            situation_type=SituationType.RECOVERY,
            limit=5,
        )
        return {
            "query": "recovery",
            "timestamp": datetime.now().timestamp(),
            "count": len(recovery),
            "situations": [s.to_dict() for s in recovery],
        }

    def statistics(self) -> Dict[str, Any]:
        stats = self._runtime.situation_history.get_statistics()
        return {
            "query": "statistics",
            "timestamp": datetime.now().timestamp(),
            "statistics": stats.to_dict(),
        }

    def severity(self) -> Dict[str, Any]:
        latest = self._runtime.situation_history.latest
        return {
            "query": "severity",
            "timestamp": datetime.now().timestamp(),
            "current_severity": latest.severity.name if latest else "NONE",
            "current_type": latest.situation_type.name if latest else "NONE",
        }

    def summary(self) -> Dict[str, Any]:
        summary_obj = self._runtime.situation_history.get_summary()
        stats = self._runtime.situation_history.get_statistics()
        return {
            "query": "summary",
            "timestamp": datetime.now().timestamp(),
            "summary": summary_obj.to_dict(),
            "statistics": stats.to_dict(),
        }
