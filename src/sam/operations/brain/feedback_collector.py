"""
OP-264 — Feedback Collector.

Collects operational feedback:
  - Rule trigger counts
  - Approval outcomes
  - Execution results
  - Anomaly events
  - Health score history
  - Mission outcomes

Provides summary statistics for learning pipeline.
"""

from __future__ import annotations

import time
from collections import defaultdict, Counter
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ── Data ───────────────────────────────────────────────────────────


@dataclass
class FeedbackEvent:
    """A single feedback event."""
    event_id: str
    event_type: str  # "rule_trigger" | "approval" | "execution" | "anomaly" | "health" | "mission"
    timestamp: float = 0.0
    source: str = ""
    value: float = 0.0
    outcome: str = "unknown"
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FeedbackSummary:
    """Aggregated feedback statistics."""
    total_events: int = 0
    by_type: Dict[str, int] = field(default_factory=dict)
    by_outcome: Dict[str, int] = field(default_factory=dict)
    approval_rate: float = 0.0
    execution_success_rate: float = 0.0
    anomaly_count: int = 0
    avg_health_score: float = 0.0
    mission_success_rate: float = 0.0
    rule_triggers: Dict[str, int] = field(default_factory=dict)
    window_hours: float = 0.0
    generated_at: float = 0.0


@dataclass
class FeedbackCollectorConfig:
    window_hours: float = 24.0
    max_events: int = 10000
    auto_summarize: bool = True


# ── Collector ──────────────────────────────────────────────────────


class FeedbackCollector:
    """
    Collect and summarize feedback events.

    Acts as the bridge between operational execution and learning.
    """

    def __init__(self, config: Optional[FeedbackCollectorConfig] = None):
        self.config = config or FeedbackCollectorConfig()
        self._events: List[FeedbackEvent] = []
        self._last_summary: Optional[FeedbackSummary] = None

    @property
    def events(self) -> List[FeedbackEvent]:
        return list(self._events)

    @property
    def last_summary(self) -> Optional[FeedbackSummary]:
        return self._last_summary

    def add(self, event: FeedbackEvent) -> None:
        """Add a single feedback event."""
        self._events.append(event)
        if len(self._events) > self.config.max_events:
            self._events.pop(0)

    def add_approval(
        self, proposal_id: str, approved: bool, source: str = "approval"
    ) -> FeedbackEvent:
        event = FeedbackEvent(
            event_id=f"approval_{proposal_id}_{int(time.time())}",
            event_type="approval",
            timestamp=time.time(),
            source=source,
            value=1.0 if approved else 0.0,
            outcome="approved" if approved else "rejected",
            metadata={"proposal_id": proposal_id},
        )
        self.add(event)
        return event

    def add_execution(
        self, mission_id: str, success: bool, duration_seconds: float = 0.0
    ) -> FeedbackEvent:
        event = FeedbackEvent(
            event_id=f"exec_{mission_id}_{int(time.time())}",
            event_type="execution",
            timestamp=time.time(),
            source="executor",
            value=1.0 if success else 0.0,
            outcome="success" if success else "failure",
            metadata={
                "mission_id": mission_id,
                "duration_seconds": duration_seconds,
            },
        )
        self.add(event)
        return event

    def add_anomaly(
        self, anomaly_type: str, severity: str = "warning", source: str = "detector"
    ) -> FeedbackEvent:
        event = FeedbackEvent(
            event_id=f"anomaly_{anomaly_type}_{int(time.time())}",
            event_type="anomaly",
            timestamp=time.time(),
            source=source,
            value=0.0,
            outcome=severity,
            metadata={"anomaly_type": anomaly_type},
        )
        self.add(event)
        return event

    def add_health_score(self, score: float) -> FeedbackEvent:
        event = FeedbackEvent(
            event_id=f"health_{int(time.time())}",
            event_type="health",
            timestamp=time.time(),
            source="health_engine",
            value=score,
            outcome="healthy" if score >= 0.8 else "degraded" if score >= 0.5 else "unhealthy",
        )
        self.add(event)
        return event

    def add_mission_outcome(
        self, mission_id: str, success: bool, mission_type: str = "general"
    ) -> FeedbackEvent:
        event = FeedbackEvent(
            event_id=f"mission_{mission_id}_{int(time.time())}",
            event_type="mission",
            timestamp=time.time(),
            source="mission_controller",
            value=1.0 if success else 0.0,
            outcome="success" if success else "failure",
            metadata={"mission_type": mission_type},
        )
        self.add(event)
        return event

    def add_rule_trigger(
        self, rule_id: str, rule_name: str, count: int = 1
    ) -> FeedbackEvent:
        event = FeedbackEvent(
            event_id=f"rule_{rule_id}_{int(time.time())}",
            event_type="rule_trigger",
            timestamp=time.time(),
            source=f"rule:{rule_id}",
            value=float(count),
            outcome="triggered",
            metadata={"rule_name": rule_name, "count": count},
        )
        self.add(event)
        return event

    def add_bulk(self, events: List[FeedbackEvent]) -> int:
        """Add multiple events. Returns count added."""
        self._events.extend(events)
        overflow = len(self._events) - self.config.max_events
        if overflow > 0:
            self._events = self._events[overflow:]
        return len(events)

    def summarize(self, window_hours: Optional[float] = None) -> FeedbackSummary:
        """Summarize events within time window."""
        window = window_hours or self.config.window_hours
        now = time.time()
        cutoff = now - (window * 3600)

        recent = [e for e in self._events if e.timestamp >= cutoff]

        if not recent:
            summary = FeedbackSummary(generated_at=now, window_hours=window)
            self._last_summary = summary
            return summary

        by_type = Counter(e.event_type for e in recent)
        by_outcome = Counter(e.outcome for e in recent)

        approvals = [e for e in recent if e.event_type == "approval"]
        approval_rate = (
            sum(1 for a in approvals if a.outcome == "approved") / len(approvals)
            if approvals else 0.0
        )

        executions = [e for e in recent if e.event_type == "execution"]
        exec_success_rate = (
            sum(1 for ex in executions if ex.outcome == "success") / len(executions)
            if executions else 0.0
        )

        anomalies = [e for e in recent if e.event_type == "anomaly"]

        health_scores = [e.value for e in recent if e.event_type == "health"]
        avg_health = sum(health_scores) / len(health_scores) if health_scores else 0.0

        missions = [e for e in recent if e.event_type == "mission"]
        mission_success_rate = (
            sum(1 for m in missions if m.outcome == "success") / len(missions)
            if missions else 0.0
        )

        rule_triggers = Counter(
            e.metadata.get("rule_name", e.source)
            for e in recent if e.event_type == "rule_trigger"
        )

        summary = FeedbackSummary(
            total_events=len(recent),
            by_type=dict(by_type),
            by_outcome=dict(by_outcome),
            approval_rate=round(approval_rate, 4),
            execution_success_rate=round(exec_success_rate, 4),
            anomaly_count=len(anomalies),
            avg_health_score=round(avg_health, 4),
            mission_success_rate=round(mission_success_rate, 4),
            rule_triggers=dict(rule_triggers),
            window_hours=window,
            generated_at=now,
        )
        self._last_summary = summary
        return summary

    def get_events_by_type(self, event_type: str) -> List[FeedbackEvent]:
        return [e for e in self._events if e.event_type == event_type]

    def get_recent_events(
        self, limit: int = 20, event_type: Optional[str] = None
    ) -> List[FeedbackEvent]:
        filtered = self._events
        if event_type:
            filtered = [e for e in filtered if e.event_type == event_type]
        return filtered[-limit:]

    def clear(self, older_than_hours: Optional[float] = None) -> int:
        """Clear events. Returns count removed."""
        if older_than_hours is None:
            removed = len(self._events)
            self._events.clear()
            return removed
        cutoff = time.time() - (older_than_hours * 3600)
        old = len([e for e in self._events if e.timestamp < cutoff])
        self._events = [e for e in self._events if e.timestamp >= cutoff]
        return old


# ── Convenience ────────────────────────────────────────────────────


def collect_feedback(
    events: Optional[List[FeedbackEvent]] = None,
) -> FeedbackSummary:
    """One-shot: collect and summarize feedback."""
    collector = FeedbackCollector()
    if events:
        collector.add_bulk(events)
    return collector.summarize()
