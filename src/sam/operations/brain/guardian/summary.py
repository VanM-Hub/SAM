"""
OP-335 — Guardian Summary Builder

Membangun ringkasan dari snapshot, history, trend, policy, recommendation.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ══════════════════════════════════════════════════════════════════════
# DTOs
# ══════════════════════════════════════════════════════════════════════

@dataclass(frozen=True)
class GuardianFinding:
    """Satu temuan."""
    finding_id: str = ""
    category: str = "info"
    severity: str = "low"
    message: str = ""
    detail: str = ""
    source: str = ""


@dataclass(frozen=True)
class GuardianRisk:
    """Satu risiko."""
    risk_id: str = ""
    category: str = ""
    severity: str = "low"
    message: str = ""
    probability: str = "low"
    impact: str = "low"
    source: str = ""


@dataclass(frozen=True)
class GuardianPriority:
    """Satu prioritas."""
    priority_id: str = ""
    urgency: str = "low"
    area: str = ""
    message: str = ""
    action: str = ""


@dataclass(frozen=True)
class GuardianSummarySection:
    """Satu section dalam summary."""
    title: str = ""
    content: str = ""
    details: Tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class GuardianSummary:
    """Ringkasan lengkap."""
    timestamp: str = ""
    current_health_status: str = "unknown"
    current_health_score: float = 0.0
    sections: Tuple[GuardianSummarySection, ...] = field(default_factory=tuple)
    findings: Tuple[GuardianFinding, ...] = field(default_factory=tuple)
    risks: Tuple[GuardianRisk, ...] = field(default_factory=tuple)
    priorities: Tuple[GuardianPriority, ...] = field(default_factory=tuple)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "current_health": self.current_health_status,
            "health_score": self.current_health_score,
            "sections": [
                {"title": s.title, "content": s.content, "details": list(s.details)}
                for s in self.sections
            ],
            "findings_count": len(self.findings),
            "risks_count": len(self.risks),
            "priorities_count": len(self.priorities),
        }


# ══════════════════════════════════════════════════════════════════════
# Summary Builder
# ══════════════════════════════════════════════════════════════════════

class GuardianSummaryBuilder:
    """Membangun GuardianSummary dari berbagai engine."""

    def __init__(
        self,
        snapshot_engine: Any = None,
        history: Any = None,
        trend: Any = None,
        policy_evaluator: Any = None,
        recommendation_engine: Any = None,
        watchdog: Any = None,
    ):
        self._snapshot = snapshot_engine
        self._history = history
        self._trend_analyzer = trend
        self._policy = policy_evaluator
        self._recommendation = recommendation_engine
        self._watchdog = watchdog
        self._summaries: List[GuardianSummary] = []

    @property
    def summary_count(self) -> int:
        return len(self._summaries)

    @property
    def last_summary(self) -> Optional[GuardianSummary]:
        return self._summaries[-1] if self._summaries else None

    def build(self, **kw: Any) -> GuardianSummary:
        """Bangun summary dari state terkini."""
        now = datetime.now().isoformat(timespec="seconds")

        # Snapshot
        snap = self._snapshot.last_snapshot if self._snapshot else None

        # Trend
        trend = self._trend_analyzer.last_trend if self._trend_analyzer else None

        health_status = snap.health.status if snap else kw.get("health_status", "unknown")
        health_score = snap.health.overall_score if snap else kw.get("health_score", 0.0)

        sections: List[GuardianSummarySection] = []

        # Section: current health
        health_detail = "Status: {}".format(health_status)
        if snap:
            health_detail += " | Score: {:.2f}".format(health_score)
            if snap.metrics.trust_level < 0.5:
                health_detail += " | Trust: LOW"
        sections.append(GuardianSummarySection(
            title="Current Health",
            content=health_status,
            details=(health_detail,),
        ))

        # Section: findings
        findings_list: List[str] = []
        if self._policy and not self._policy.all_passed:
            findings_list.append("{} policy violations".format(len(self._policy.violations)))
        if self._watchdog and len(self._watchdog.alerts) > 0:
            findings_list.append("{} watchdog alerts".format(len(self._watchdog.alerts)))
        if self._watchdog and len(self._watchdog.warnings) > 0:
            findings_list.append("{} warnings".format(len(self._watchdog.warnings)))
        if snap and snap.metrics.provider_unhealthy > 0:
            findings_list.append("{} unhealthy providers".format(snap.metrics.provider_unhealthy))

        sections.append(GuardianSummarySection(
            title="Findings",
            content="{} findings".format(len(findings_list)),
            details=tuple(findings_list),
        ))

        # Section: policy violations
        violation_details: List[str] = []
        if self._policy and self._policy.violations:
            for v in self._policy.violations[:5]:
                violation_details.append("{} (severity: {})".format(v.policy, v.severity))
        sections.append(GuardianSummarySection(
            title="Policy Violations",
            content="{} violations".format(len(self._policy.violations) if self._policy else 0),
            details=tuple(violation_details),
        ))

        # Section: recommendations
        rec_details: List[str] = []
        if self._recommendation and self._recommendation.recommendations:
            for r in self._recommendation.recommendations[:5]:
                rec_details.append("{} (priority: {})".format(
                    r.recommendation_type, r.priority,
                ))
        sections.append(GuardianSummarySection(
            title="Recommendations",
            content="{} recommendations".format(
                len(self._recommendation.recommendations) if self._recommendation else 0,
            ),
            details=tuple(rec_details),
        ))

        # Section: risks
        risk_details: List[str] = []
        if trend:
            for s in trend.signals:
                risk_details.append("Signal: {}".format(s))
            for p in trend.patterns:
                risk_details.append("Pattern: {}".format(p))
        sections.append(GuardianSummarySection(
            title="Risks",
            content="{} signals, {} patterns".format(
                len(trend.signals) if trend else 0,
                len(trend.patterns) if trend else 0,
            ),
            details=tuple(risk_details),
        ))

        # Section: priorities
        priority_details: List[str] = []
        if self._recommendation and self._recommendation.recommendations:
            for r in self._recommendation.recommendations:
                if r.priority in ("critical", "high"):
                    priority_details.append("{} (source: {})".format(
                        r.recommendation_type, r.source,
                    ))
        sections.append(GuardianSummarySection(
            title="Priorities",
            content="{} urgent actions".format(len(priority_details)),
            details=tuple(priority_details[:5]),
        ))

        # Build findings
        findings: list[GuardianFinding] = []
        if self._policy and not self._policy.all_passed:
            for v in self._policy.violations:
                findings.append(GuardianFinding(
                    category="policy",
                    severity=v.severity,
                    message=v.policy,
                    detail=v.message,
                    source="policy_evaluator",
                ))

        # Build risks
        risks: list[GuardianRisk] = []
        if trend:
            for s in trend.signals:
                risks.append(GuardianRisk(
                    category="signal",
                    severity="medium",
                    message=s,
                    source="trend_analyzer",
                ))
            for p in trend.patterns:
                risks.append(GuardianRisk(
                    category="pattern",
                    severity="high",
                    message=p,
                    source="trend_analyzer",
                ))

        # Build priorities
        priorities: list[GuardianPriority] = []
        if self._recommendation:
            for r in self._recommendation.recommendations:
                if r.priority == "critical":
                    priorities.append(GuardianPriority(
                        urgency="critical",
                        area=r.source,
                        message=r.recommendation_type,
                        action=r.title,
                    ))

        summary = GuardianSummary(
            timestamp=now,
            current_health_status=health_status,
            current_health_score=health_score,
            sections=tuple(sections),
            findings=tuple(findings),
            risks=tuple(risks),
            priorities=tuple(priorities),
        )

        self._summaries.append(summary)
        return summary
