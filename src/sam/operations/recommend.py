"""
RecommendationEngine — Actionable recommendations berbasis evidence.

Setiap rekomendasi wajib memiliki:
  reason, priority, impact, urgency, expected outcome, required evidence
Tidak boleh ada generic recommendation.
"""

import structlog
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


logger = structlog.get_logger()


PRIORITY_MAP = {"critical": 1, "high": 2, "medium": 3, "low": 4}
URGENCY_MAP = {"immediate": 1, "today": 2, "this_week": 3, "this_month": 4}


@dataclass
class ActionableRecommendation:
    """Satu rekomendasi dengan evidence lengkap."""
    action: str                 # "Clean up cache"
    reason: str                 # "Cache exceeded 700MB"
    priority: str               # "critical" | "high" | "medium" | "low"
    impact: str                 # "Prevent storage exhaustion"
    urgency: str                # "immediate" | "today" | "this_week" | "this_month"
    expected_outcome: str       # "Free up 500MB of disk space"
    required_evidence: List[str] = field(default_factory=list)
    source: str = "recommendation_engine"

    def to_text(self) -> str:
        return "[{priority}] {action} — {reason}. Impact: {impact}. Expected: {expected_outcome}.".format(
            priority=self.priority.upper(),
            action=self.action,
            reason=self.reason,
            impact=self.impact,
            expected_outcome=self.expected_outcome,
        )


class RecommendationEngine:
    """Menghasilkan actionable recommendations dari anomali dan observasi."""

    def __init__(self, anomaly_detector=None, runtime_provider=None, workspace_provider=None):
        self._ad = anomaly_detector
        self._rp = runtime_provider
        self._wp = workspace_provider

    def recommend_all(self) -> List[ActionableRecommendation]:
        """Kumpulkan semua rekomendasi dari semua sumber."""
        recommendations = []

        # Dari anomali
        if self._ad:
            anomalies = self._ad.detect_all()
            recommendations.extend(self._from_anomalies(anomalies))

        # Dari workspace langsung
        if self._wp:
            ws = self._wp.observe()
            recommendations.extend(self._from_workspace(ws))

        # Dari runtime
        if self._rp:
            snap = self._rp.get_latest()
            if snap:
                recommendations.extend(self._from_runtime(snap))

        # Urutkan prioritas
        recommendations.sort(key=lambda r: PRIORITY_MAP.get(r.priority, 99))

        logger.info("recommendations_completed",
            count=len(recommendations),
            priorities=[r.priority for r in recommendations[:5]],
        )
        return recommendations

    def _from_anomalies(self, anomalies) -> List[ActionableRecommendation]:
        recs = []
        for a in anomalies:
            if a.type == "database_unavailable":
                recs.append(ActionableRecommendation(
                    action="Reconnect database",
                    reason="Database is unavailable",
                    priority="critical",
                    impact="System operations requiring database access will fail",
                    urgency="immediate",
                    expected_outcome="Restore database connectivity",
                    required_evidence=a.evidence,
                ))
            elif a.type == "disk_exhaustion":
                recs.append(ActionableRecommendation(
                    action="Free up disk space",
                    reason="Disk at {:.1f}% capacity".format(a.value) if a.value else "Disk near full",
                    priority="high" if a.severity == "warning" else "critical",
                    impact="Prevent storage exhaustion and write failures",
                    urgency="today" if a.severity == "warning" else "immediate",
                    expected_outcome="Reduce disk usage below 80%",
                    required_evidence=a.evidence,
                ))
            elif a.type == "cpu_spike":
                recs.append(ActionableRecommendation(
                    action="Investigate CPU spike",
                    reason="CPU at {:.1f}%".format(a.value) if a.value else "CPU spike detected",
                    priority="high",
                    impact="May cause operation latency and queue buildup",
                    urgency="today",
                    expected_outcome="CPU returns to normal range",
                    required_evidence=a.evidence,
                ))
            elif a.type == "queue_growth":
                recs.append(ActionableRecommendation(
                    action="Drain pending queue",
                    reason="Queue depth: {} (threshold: {})".format(a.value, a.threshold),
                    priority="high",
                    impact="Pending operations may cause delays or failures",
                    urgency="today",
                    expected_outcome="Queue returns to idle or healthy state",
                    required_evidence=a.evidence,
                ))
            elif a.type == "memory_high":
                recs.append(ActionableRecommendation(
                    action="Investigate memory usage",
                    reason="Memory at {:.1f}%".format(a.value) if a.value else "Memory spike detected",
                    priority="high",
                    impact="May cause OOM or process termination",
                    urgency="today",
                    expected_outcome="Memory usage drops below 85%",
                    required_evidence=a.evidence,
                ))
            elif a.type == "temp_accumulation":
                recs.append(ActionableRecommendation(
                    action="Clean up temp files",
                    reason="Temp files: {} ({:.1f} MB)".format(a.value, a.value) if a.value else "Temp accumulation",
                    priority="medium",
                    impact="Free up disk space and reduce clutter",
                    urgency="this_week",
                    expected_outcome="Remove temporary files, free up space",
                    required_evidence=a.evidence,
                ))
            elif a.type == "cache_explosion":
                recs.append(ActionableRecommendation(
                    action="Clean up cache",
                    reason="Cache at {:.1f} MB".format(a.value) if a.value else "Cache too large",
                    priority="medium",
                    impact="Reduce disk usage and improve performance",
                    urgency="this_week",
                    expected_outcome="Free up cache space",
                    required_evidence=a.evidence,
                ))
        return recs

    def _from_workspace(self, ws) -> List[ActionableRecommendation]:
        recs = []

        # Database
        if ws.database.status.lower() == "unavailable":
            # Already handled by anomaly detector — skip dup
            pass

        # Temp accumulation (detail)
        if ws.temp.count > 200:
            recs.append(ActionableRecommendation(
                action="Remove temp files ({} files, {:.1f} MB)".format(ws.temp.count, ws.temp.size_mb),
                reason="Temp files exceeded {} files".format(ws.temp.count),
                priority="medium",
                impact="Free {:.1f} MB disk space".format(ws.temp.size_mb),
                urgency="this_week",
                expected_outcome="Remove {} temp files, free {:.1f} MB".format(ws.temp.count, ws.temp.size_mb),
                required_evidence=["Temp files: {} ({:.1f} MB)".format(ws.temp.count, ws.temp.size_mb)],
            ))

        # Cache
        if ws.cache.size_mb > 100:
            recs.append(ActionableRecommendation(
                action="Cleanup cache ({:.1f} MB, {} files)".format(ws.cache.size_mb, ws.cache.file_count),
                reason="Cache size exceeded 100 MB",
                priority="low",
                impact="Free disk space and improve I/O performance",
                urgency="this_month",
                expected_outcome="Reduce cache to under 100 MB",
                required_evidence=["Cache: {:.1f} MB ({} files)".format(ws.cache.size_mb, ws.cache.file_count)],
            ))

        return recs

    def _from_runtime(self, snap) -> List[ActionableRecommendation]:
        recs = []

        # Uptime rendah
        if snap.uptime_seconds < 300 and snap.uptime_seconds > 0:
            recs.append(ActionableRecommendation(
                action="Monitor system after restart",
                reason="System restarted {:.0f}s ago".format(snap.uptime_seconds),
                priority="low",
                impact="Early detection of post-restart issues",
                urgency="today",
                expected_outcome="System stabilizes within 5 minutes",
                required_evidence=["Uptime: {:.0f}s".format(snap.uptime_seconds)],
            ))

        # Queue growing
        if snap.queue_status == "growing":
            recs.append(ActionableRecommendation(
                action="Increase processing capacity",
                reason="Queue is growing (depth: {}, throughput: {:.1f} ops/s)".format(
                    snap.queue_depth, snap.throughput
                ),
                priority="high",
                impact="Prevent queue overflow and operation timeouts",
                urgency="today",
                expected_outcome="Queue drains below {} operations".format(snap.queue_depth),
                required_evidence=[
                    "Queue status: {}".format(snap.queue_status),
                    "Queue depth: {}".format(snap.queue_depth),
                    "Throughput: {:.1f} ops/s".format(snap.throughput),
                ],
            ))

        return recs
