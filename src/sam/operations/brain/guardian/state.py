"""
OP-314 — Guardian State

DTO untuk state guardian:
  - GuardianState
  - GuardianHealth
  - GuardianStatistics
  - GuardianSnapshot

Semua frozen.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class GuardianState:
    status: str  # active, paused, degraded, stopped
    pipeline_running: bool = False
    gate_active: bool = True
    policy_enabled: bool = True
    audit_active: bool = True
    last_pipeline_at: str = ""
    error_count: int = 0
    started_at: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "pipeline_running": self.pipeline_running,
            "gate_active": self.gate_active,
            "policy_enabled": self.policy_enabled,
            "audit_active": self.audit_active,
            "last_pipeline_at": self.last_pipeline_at,
            "error_count": self.error_count,
            "started_at": self.started_at,
        }


@dataclass(frozen=True)
class GuardianHealth:
    overall: str  # green, yellow, red
    coordinator_healthy: bool = True
    gate_healthy: bool = True
    policy_healthy: bool = True
    audit_healthy: bool = True
    conversation_healthy: bool = True
    dashboard_healthy: bool = True
    last_health_check: str = ""
    issues: Tuple[str, ...] = ()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall": self.overall,
            "coordinator_healthy": self.coordinator_healthy,
            "gate_healthy": self.gate_healthy,
            "policy_healthy": self.policy_healthy,
            "audit_healthy": self.audit_healthy,
            "conversation_healthy": self.conversation_healthy,
            "dashboard_healthy": self.dashboard_healthy,
            "last_health_check": self.last_health_check,
            "issues": list(self.issues),
        }


@dataclass(frozen=True)
class GuardianStatistics:
    total_pipelines: int = 0
    passed_gate: int = 0
    rejected_gate: int = 0
    policy_violations: int = 0
    approvals_waiting: int = 0
    approvals_completed: int = 0
    reasonings_completed: int = 0
    proposals_submitted: int = 0
    average_pipeline_ms: float = 0.0
    uptime_hours: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_pipelines": self.total_pipelines,
            "passed_gate": self.passed_gate,
            "rejected_gate": self.rejected_gate,
            "policy_violations": self.policy_violations,
            "approvals_waiting": self.approvals_waiting,
            "approvals_completed": self.approvals_completed,
            "reasonings_completed": self.reasonings_completed,
            "proposals_submitted": self.proposals_submitted,
            "average_pipeline_ms": self.average_pipeline_ms,
            "uptime_hours": self.uptime_hours,
        }


@dataclass(frozen=True)
class GuardianSnapshot:
    state: GuardianState
    health: GuardianHealth
    statistics: GuardianStatistics
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "state": self.state.to_dict(),
            "health": self.health.to_dict(),
            "statistics": self.statistics.to_dict(),
            "timestamp": self.timestamp,
        }
