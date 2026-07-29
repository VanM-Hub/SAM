"""
OP-337 — Dashboard Guardian V2

DTO only — tidak ada renderer.
Kartu dashboard immutable yang digunakan oleh runtime & conversation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════
# DTOs
# ══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GuardianHealthCard:
    """Health status card."""
    status: str = "unknown"
    score: float = 0.0
    issues_count: int = 0
    issues: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "score": self.score,
            "issues_count": self.issues_count,
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class GuardianPolicyCard:
    """Policy compliance card."""
    all_passed: bool = True
    violations_count: int = 0
    violations: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "all_passed": self.all_passed,
            "violations_count": self.violations_count,
            "violations": list(self.violations),
        }


@dataclass(frozen=True)
class GuardianTrendCard:
    """Trend card."""
    health_trend: str = "stable"
    recommendation_trend: str = "stable"
    watchdog_trend: str = "stable"
    policy_trend: str = "stable"
    anomaly_trend: str = "stable"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health_trend": self.health_trend,
            "recommendation_trend": self.recommendation_trend,
            "watchdog_trend": self.watchdog_trend,
            "policy_trend": self.policy_trend,
            "anomaly_trend": self.anomaly_trend,
        }


@dataclass(frozen=True)
class GuardianRecommendationCard:
    """Recommendation card."""
    count: int = 0
    critical_count: int = 0
    high_count: int = 0
    items: Tuple[Dict[str, Any], ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "critical_count": self.critical_count,
            "high_count": self.high_count,
            "items": list(self.items),
        }


@dataclass(frozen=True)
class GuardianRiskCard:
    """Risk card."""
    count: int = 0
    signals: Tuple[str, ...] = field(default_factory=tuple)
    patterns: Tuple[str, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "count": self.count,
            "signals": list(self.signals),
            "patterns": list(self.patterns),
        }


@dataclass(frozen=True)
class GuardianSummaryCard:
    """Summary card."""
    health_status: str = "unknown"
    health_score: float = 0.0
    findings_count: int = 0
    risks_count: int = 0
    priorities_count: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "health_status": self.health_status,
            "health_score": self.health_score,
            "findings_count": self.findings_count,
            "risks_count": self.risks_count,
            "priorities_count": self.priorities_count,
        }


# ══════════════════════════════════════════════════════════════════════
# Dashboard V2 Service
# ══════════════════════════════════════════════════════════════════════

class GuardianDashboardV2Service:
    """Membangun dashboard cards dari engine — no renderer."""

    def __init__(
        self,
        health_engine: Any = None,
        policy_evaluator: Any = None,
        trend_analyzer: Any = None,
        recommendation_engine: Any = None,
        summary_builder: Any = None,
        snapshot_engine: Any = None,
    ):
        self._health = health_engine
        self._policy = policy_evaluator
        self._trend = trend_analyzer
        self._recommendation = recommendation_engine
        self._summary = summary_builder
        self._snapshot = snapshot_engine

    def build_health_card(self) -> GuardianHealthCard:
        h = self._health.latest() if self._health else None
        if h:
            return GuardianHealthCard(
                status=h.status,
                score=h.score.overall_score,
                issues_count=len(h.issues),
                issues=tuple(i.message for i in h.issues),
            )
        return GuardianHealthCard()

    def build_policy_card(self) -> GuardianPolicyCard:
        if self._policy:
            return GuardianPolicyCard(
                all_passed=self._policy.all_passed,
                violations_count=len(self._policy.violations),
                violations=tuple("{}: {}".format(v.policy, v.message)
                                 for v in self._policy.violations),
            )
        return GuardianPolicyCard()

    def build_trend_card(self) -> GuardianTrendCard:
        t = self._trend.last_trend if self._trend else None
        if t:
            return GuardianTrendCard(
                health_trend=t.health_trend,
                recommendation_trend=t.recommendation_trend,
                watchdog_trend=t.watchdog_trend,
                policy_trend=t.policy_trend,
                anomaly_trend=t.anomaly_trend,
            )
        return GuardianTrendCard()

    def build_recommendation_card(self) -> GuardianRecommendationCard:
        if self._recommendation:
            recs = self._recommendation.recommendations
            critical = sum(1 for r in recs if r.priority == "critical")
            high = sum(1 for r in recs if r.priority == "high")
            return GuardianRecommendationCard(
                count=len(recs),
                critical_count=critical,
                high_count=high,
                items=tuple(
                    {"type": r.recommendation_type, "priority": r.priority,
                     "source": r.source, "title": r.title}
                    for r in recs
                ),
            )
        return GuardianRecommendationCard()

    def build_risk_card(self) -> GuardianRiskCard:
        t = self._trend.last_trend if self._trend else None
        if t:
            return GuardianRiskCard(
                count=len(t.signals) + len(t.patterns),
                signals=t.signals,
                patterns=t.patterns,
            )
        return GuardianRiskCard()

    def build_summary_card(self) -> GuardianSummaryCard:
        sm = self._summary.last_summary if self._summary else None
        snap = self._snapshot.last_snapshot if self._snapshot else None
        health_status = (snap.health.status if snap else
                         sm.current_health_status if sm else "unknown")
        health_score = (snap.health.overall_score if snap else
                        sm.current_health_score if sm else 0.0)
        findings = len(sm.findings) if sm else 0
        risks = len(sm.risks) if sm else 0
        priorities = len(sm.priorities) if sm else 0
        return GuardianSummaryCard(
            health_status=health_status,
            health_score=health_score,
            findings_count=findings,
            risks_count=risks,
            priorities_count=priorities,
        )
