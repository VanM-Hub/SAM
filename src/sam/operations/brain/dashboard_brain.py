"""
OP-266 — Dashboard Brain.

Upgraded dashboard for Sprint 21.

Menambahkan insight otomatis ke dashboard:
  - Approval bottleneck trends
  - Mission recovery patterns
  - Failure pattern trends
  - Health score trajectory
  - Learning progress

All deterministic, no ML/AI.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class Insight:
    """A single operational insight."""
    insight_id: str
    title: str
    description: str
    category: str  # "approval" | "mission" | "failure" | "health" | "learning"
    severity: str  # "info" | "warning" | "critical"
    value: float = 0.0
    change_pct: float = 0.0
    trend: str = "stable"  # "improving" | "declining" | "stable"
    confidence: float = 0.8
    generated_at: float = 0.0
    actions: List[str] = field(default_factory=list)
    data: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "insight_id": self.insight_id,
            "title": self.title,
            "description": self.description,
            "category": self.category,
            "severity": self.severity,
            "value": self.value,
            "change_pct": round(self.change_pct, 1),
            "trend": self.trend,
            "confidence": self.confidence,
        }


@dataclass
class DashboardStateV2:
    """
    Expanded dashboard state with learning insights.

    Inherits base dashboard fields + new insights.
    """
    # Base fields (from DashboardState)
    observation_summary: Dict[str, Any] = field(default_factory=dict)
    health_score: float = 1.0
    health_state: str = "healthy"
    active_mission_count: int = 0
    pending_approval_count: int = 0
    anomaly_count: int = 0
    rule_triggered_count: int = 0
    recommendation_count: int = 0
    total_proposals: int = 0

    # Sprint 21 additions
    insights: List[Insight] = field(default_factory=list)
    patterns_found: int = 0
    feedback_events: int = 0
    optimizations_applied: int = 0
    learning_progress: float = 0.0
    snapshot_version: str = ""
    last_insight_generated: float = 0.0


# ── Insight Engine ─────────────────────────────────────────────────


class DashboardBrainV2:
    """
    Upgraded dashboard brain with automatic insight generation.

    Generates insights from:
      - Feedback summary
      - Pattern discovery results
      - Optimization reports
      - Health score history
      - Approval/mission/learning trends
    """

    def __init__(self):
        self._last_state: Optional[DashboardStateV2] = None
        self._health_history: List[float] = []
        self._approval_rate_history: List[float] = []
        self._mission_rate_history: List[float] = []

    @property
    def last_state(self) -> Optional[DashboardStateV2]:
        return self._last_state

    def compute(
        self,
        observation_summary: Optional[Dict[str, Any]] = None,
        health_score: float = 1.0,
        health_state: str = "healthy",
        insights_from_feedback: Optional[List[Insight]] = None,
        patterns_found: int = 0,
        feedback_events: int = 0,
        optimizations_applied: int = 0,
        approval_rate: float = 0.0,
        mission_success_rate: float = 0.0,
        learning_progress: float = 0.0,
        snapshot_version: str = "",
    ) -> DashboardStateV2:
        """Compute dashboard state with automatic insights."""
        # Track history
        self._health_history.append(health_score)
        if len(self._health_history) > 10:
            self._health_history = self._health_history[-10:]
        self._approval_rate_history.append(approval_rate)
        if len(self._approval_rate_history) > 10:
            self._approval_rate_history = self._approval_rate_history[-10:]
        self._mission_rate_history.append(mission_success_rate)
        if len(self._mission_rate_history) > 10:
            self._mission_rate_history = self._mission_rate_history[-10:]

        # Build base observation summary
        base_summary = observation_summary or {
            "active_missions": 0,
            "pending_approvals": 0,
            "anomalies": 0,
            "queue_length": 0,
        }

        state = DashboardStateV2(
            observation_summary=base_summary,
            health_score=health_score,
            health_state=health_state,
            active_mission_count=base_summary.get("active_missions", 0),
            pending_approval_count=base_summary.get("pending_approvals", 0),
            anomaly_count=base_summary.get("anomalies", 0),
            rule_triggered_count=base_summary.get("rule_triggers", 0),
            recommendation_count=base_summary.get("recommendations", 0),
            total_proposals=base_summary.get("proposals", 0),
            insights=insights_from_feedback or self._generate_insights(
                health_score=health_score,
                approval_rate=approval_rate,
                mission_success_rate=mission_success_rate,
                patterns_found=patterns_found,
            ),
            patterns_found=patterns_found,
            feedback_events=feedback_events,
            optimizations_applied=optimizations_applied,
            learning_progress=round(learning_progress, 4),
            snapshot_version=snapshot_version,
            last_insight_generated=time.time(),
        )
        self._last_state = state
        return state

    # ── Insight generation ─────────────────────────────────────────

    def _generate_insights(
        self,
        health_score: float,
        approval_rate: float,
        mission_success_rate: float,
        patterns_found: int,
    ) -> List[Insight]:
        """Generate automatic insights from tracked data."""
        insights: List[Insight] = []

        # 1. Health trajectory
        health_insight = self._health_trend_insight(health_score)
        if health_insight:
            insights.append(health_insight)

        # 2. Approval bottleneck insight
        approval_insight = self._approval_trend_insight(approval_rate)
        if approval_insight:
            insights.append(approval_insight)

        # 3. Mission recovery insight
        mission_insight = self._mission_trend_insight(mission_success_rate)
        if mission_insight:
            insights.append(mission_insight)

        # 4. Learning progress insight
        if patterns_found > 0:
            insights.append(Insight(
                insight_id="learning_progress",
                title="Pattern Discovery Active",
                description=f"Found {patterns_found} operational patterns in recent data",
                category="learning",
                severity="info",
                value=float(patterns_found),
                trend="improving" if patterns_found > 0 else "stable",
                confidence=0.8,
                actions=["Review discovered patterns", "Update knowledge snapshot"],
            ))

        # 5. Overall trend insight
        if len(self._health_history) >= 3:
            old_avg = sum(self._health_history[:-2]) / len(self._health_history[:-2])
            new_avg = sum(self._health_history[-2:]) / 2
            if abs(new_avg - old_avg) > 0.05:
                insights.append(Insight(
                    insight_id="system_trend",
                    title="System Health Trend",
                    description=f"Health {'improving' if new_avg > old_avg else 'declining'} "
                                f"({old_avg:.2f} → {new_avg:.2f})",
                    category="health",
                    severity="info" if new_avg >= old_avg else "warning",
                    value=new_avg,
                    change_pct=((new_avg - old_avg) / old_avg * 100) if old_avg else 0,
                    trend="improving" if new_avg >= old_avg else "declining",
                ))

        return insights

    def _health_trend_insight(self, current_health: float) -> Optional[Insight]:
        if len(self._health_history) < 3:
            return None
        recent = self._health_history[-3:]
        trend = "improving" if all(recent[i] <= recent[i+1] for i in range(len(recent)-1)) else \
                "declining" if all(recent[i] >= recent[i+1] for i in range(len(recent)-1)) else "stable"
        change = ((recent[-1] - recent[0]) / max(recent[0], 0.01)) * 100
        if abs(change) < 2:
            return None
        severity = "warning" if trend == "declining" and current_health < 0.7 else "info"
        return Insight(
            insight_id="health_trend",
            title="Health Score Trajectory",
            description=f"Health score {'improved' if trend == 'improving' else 'declined'} "
                        f"by {abs(change):.1f}% over last 3 cycles "
                        f"({recent[0]:.2f} → {recent[-1]:.2f})",
            category="health",
            severity=severity,
            value=current_health,
            change_pct=round(change, 1),
            trend=trend,
        )

    def _approval_trend_insight(self, current_rate: float) -> Optional[Insight]:
        if len(self._approval_rate_history) < 3:
            return None
        recent = self._approval_rate_history[-3:]
        trend = "improving" if all(recent[i] <= recent[i+1] for i in range(len(recent)-1)) else \
                "declining" if all(recent[i] >= recent[i+1] for i in range(len(recent)-1)) else "stable"
        if trend == "declining" and current_rate < 0.6:
            return Insight(
                insight_id="approval_bottleneck",
                title="Approval Bottleneck",
                description=f"Approval rate declining: {recent[0]:.0%} → {current_rate:.0%}",
                category="approval",
                severity="warning",
                value=current_rate,
                change_pct=round(((current_rate - recent[0]) / max(recent[0], 0.01)) * 100, 1),
                trend=trend,
                actions=["Review pending approvals", "Escalate stalled proposals"],
            )
        if trend == "improving" and current_rate > 0.8:
            return Insight(
                insight_id="approval_recovery",
                title="Approval Recovery",
                description=f"Approval rate improved: {recent[0]:.0%} → {current_rate:.0%}",
                category="approval",
                severity="info",
                value=current_rate,
                trend=trend,
            )
        return Insight(
            insight_id="approval_stable",
            title="Approval Workflow",
            description=f"Approval rate: {current_rate:.0%} ({trend})",
            category="approval",
            severity="info",
            value=current_rate,
            trend=trend,
        )

    def _mission_trend_insight(self, current_rate: float) -> Optional[Insight]:
        if len(self._mission_rate_history) < 3:
            return None
        recent = self._mission_rate_history[-3:]
        trend = "improving" if all(recent[i] <= recent[i+1] for i in range(len(recent)-1)) else \
                "declining" if all(recent[i] >= recent[i+1] for i in range(len(recent)-1)) else "stable"
        if trend == "improving":
            return Insight(
                insight_id="mission_recovery",
                title="Mission Recovery Improving",
                description=f"Mission success rate: {recent[0]:.0%} → {current_rate:.0%}",
                category="mission",
                severity="info",
                value=current_rate,
                change_pct=round(((current_rate - recent[0]) / max(recent[0], 0.01)) * 100, 1),
                trend=trend,
                actions=["Review mission logs for improvements"],
            )
        if trend == "declining" and current_rate < 0.5:
            return Insight(
                insight_id="mission_decline",
                title="Mission Success Declining",
                description=f"Mission success rate dropped: {recent[0]:.0%} → {current_rate:.0%}",
                category="mission",
                severity="critical",
                value=current_rate,
                trend=trend,
                actions=["Investigate recent failures", "Roll back recent changes"],
            )
        return None


# ── Convenience ────────────────────────────────────────────────────


def compute_dashboard(
    health_score: float = 1.0,
    approval_rate: float = 1.0,
    mission_success_rate: float = 1.0,
    patterns_found: int = 0,
) -> DashboardStateV2:
    """One-shot: compute dashboard with insights."""
    brain = DashboardBrainV2()
    return brain.compute(
        health_score=health_score,
        approval_rate=approval_rate,
        mission_success_rate=mission_success_rate,
        patterns_found=patterns_found,
    )
