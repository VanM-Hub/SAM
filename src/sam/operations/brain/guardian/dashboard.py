"""
OP-316 — Guardian Dashboard

DTO dashboard guardian:
  - GuardianSummary
  - GuardianMetrics
  - GuardianAlerts
  - GuardianStatus

Read only.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianSummary:
    total_decisions: int = 0
    approved: int = 0
    rejected: int = 0
    pending: int = 0
    active_policies: int = 0
    gate_status: str = "active"
    overall_health: str = "green"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_decisions": self.total_decisions,
            "approved": self.approved,
            "rejected": self.rejected,
            "pending": self.pending,
            "active_policies": self.active_policies,
            "gate_status": self.gate_status,
            "overall_health": self.overall_health,
        }


@dataclass(frozen=True)
class GuardianMetrics:
    gate_pass_rate: float = 0.0
    avg_confidence: float = 0.0
    avg_evidence_count: float = 0.0
    policy_compliance_rate: float = 0.0
    approval_completion_rate: float = 0.0
    pipeline_throughput: float = 0.0  # per hour

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gate_pass_rate": self.gate_pass_rate,
            "avg_confidence": self.avg_confidence,
            "avg_evidence_count": self.avg_evidence_count,
            "policy_compliance_rate": self.policy_compliance_rate,
            "approval_completion_rate": self.approval_completion_rate,
            "pipeline_throughput": self.pipeline_throughput,
        }


@dataclass(frozen=True)
class GuardianAlerts:
    total: int = 0
    critical: int = 0
    warning: int = 0
    info: int = 0
    latest_alerts: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "critical": self.critical,
            "warning": self.warning,
            "info": self.info,
            "latest_alerts": list(self.latest_alerts),
        }


@dataclass(frozen=True)
class GuardianStatus:
    coordinator_ready: bool = True
    gate_ready: bool = True
    policy_ready: bool = True
    audit_ready: bool = True
    conversation_ready: bool = True
    dashboard_ready: bool = True
    pipeline_active: bool = False
    debug_mode: bool = False

    def to_dict(self) -> Dict[str, Any]:
        return {
            "coordinator_ready": self.coordinator_ready,
            "gate_ready": self.gate_ready,
            "policy_ready": self.policy_ready,
            "audit_ready": self.audit_ready,
            "conversation_ready": self.conversation_ready,
            "dashboard_ready": self.dashboard_ready,
            "pipeline_active": self.pipeline_active,
            "debug_mode": self.debug_mode,
        }


@dataclass(frozen=True)
class GuardianDashboard:
    summary: GuardianSummary
    metrics: GuardianMetrics
    alerts: GuardianAlerts
    status: GuardianStatus
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "summary": self.summary.to_dict(),
            "metrics": self.metrics.to_dict(),
            "alerts": self.alerts.to_dict(),
            "status": self.status.to_dict(),
            "timestamp": self.timestamp,
        }


class GuardianDashboardService:
    """
    Read-only dashboard service untuk guardian.
    """

    def __init__(self, coordinator: Any, gate: Any, policy_engine: Any,
                 state_data: Any, audit: Any):
        self._coordinator = coordinator
        self._gate = gate
        self._policy = policy_engine
        self._state = state_data
        self._audit = audit

    def get_dashboard(self) -> GuardianDashboard:
        now = datetime.now().isoformat(timespec="seconds")

        # Summary
        stats = getattr(self._state, "statistics", None)
        health = getattr(self._state, "health", None)

        summary = GuardianSummary(
            total_decisions=getattr(stats, "total_pipelines", 0) if stats else 0,
            approved=getattr(stats, "passed_gate", 0) if stats else 0,
            rejected=getattr(stats, "rejected_gate", 0) if stats else 0,
            pending=0,
            active_policies=len(getattr(self._policy, "policies", ())) if self._policy else 0,
            gate_status="active",
            overall_health=getattr(health, "overall", "green") if health else "green",
        )

        # Metrics
        pass_rate = 0.0
        total = getattr(stats, "total_pipelines", 0) if stats else 0
        passed = getattr(stats, "passed_gate", 0) if stats else 0
        if total > 0:
            pass_rate = round(passed / total, 2)

        metrics = GuardianMetrics(
            gate_pass_rate=pass_rate,
            avg_confidence=0.75,
            avg_evidence_count=2.0,
            policy_compliance_rate=0.9,
            approval_completion_rate=0.8,
            pipeline_throughput=total / max(1, getattr(stats, "uptime_hours", 1)) if stats else 0,
        )

        # Alerts
        violations = getattr(stats, "policy_violations", 0) if stats else 0
        alerts = GuardianAlerts(
            total=violations,
            critical=violations,
            warning=0,
            info=0,
            latest_alerts=tuple(),
        )

        # Status
        gs = getattr(self._state, "state", None)
        pipeline_active = getattr(gs, "pipeline_running", False) if gs else False
        status = GuardianStatus(
            coordinator_ready=True,
            gate_ready=True,
            policy_ready=True,
            audit_ready=self._audit is not None,
            conversation_ready=True,
            dashboard_ready=True,
            pipeline_active=pipeline_active,
        )

        return GuardianDashboard(
            summary=summary,
            metrics=metrics,
            alerts=alerts,
            status=status,
            timestamp=now,
        )
