"""
OP-321 — Guardian Supervisor

Mengawasi seluruh Guardian Runtime dengan menerima snapshot dari:
  - Reasoning
  - Decision
  - Brain
  - Mission
  - Scheduler
  - Provider

Output: GuardianSupervisorSnapshot (immutable DTO)
Constraint: read-only, no execution, no domain calls.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from datetime import datetime


# ── DTOs ──────────────────────────────────────────────────────────────────

@dataclass(frozen=True)
class ReasoningStatus:
    active_sessions: int = 0
    completed_count: int = 0
    failed_count: int = 0
    average_duration_ms: float = 0.0
    last_completed_at: str = ""


@dataclass(frozen=True)
class DecisionStatus:
    total_decisions: int = 0
    pending_approvals: int = 0
    approved_count: int = 0
    rejected_count: int = 0


@dataclass(frozen=True)
class BrainStatus:
    pipeline_active: bool = False
    observation_running: bool = False
    health_check_ok: bool = True
    error_count: int = 0


@dataclass(frozen=True)
class MissionStatus:
    active_missions: int = 0
    completed_missions: int = 0
    failed_missions: int = 0
    stalled_missions: int = 0


@dataclass(frozen=True)
class SchedulerStatus:
    tasks_queued: int = 0
    tasks_running: int = 0
    tasks_completed: int = 0
    overloaded: bool = False


@dataclass(frozen=True)
class ProviderStatus:
    active_providers: int = 0
    healthy_providers: int = 0
    degraded_providers: int = 0
    last_check_at: str = ""


@dataclass(frozen=True)
class GuardianSupervisorSnapshot:
    reasoning: ReasoningStatus = field(default_factory=ReasoningStatus)
    decision: DecisionStatus = field(default_factory=DecisionStatus)
    brain: BrainStatus = field(default_factory=BrainStatus)
    mission: MissionStatus = field(default_factory=MissionStatus)
    scheduler: SchedulerStatus = field(default_factory=SchedulerStatus)
    provider: ProviderStatus = field(default_factory=ProviderStatus)
    timestamp: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {
            "reasoning": {
                "active_sessions": self.reasoning.active_sessions,
                "completed_count": self.reasoning.completed_count,
                "failed_count": self.reasoning.failed_count,
                "average_duration_ms": self.reasoning.average_duration_ms,
            },
            "decision": {
                "total_decisions": self.decision.total_decisions,
                "pending_approvals": self.decision.pending_approvals,
                "approved_count": self.decision.approved_count,
                "rejected_count": self.decision.rejected_count,
            },
            "brain": {
                "pipeline_active": self.brain.pipeline_active,
                "observation_running": self.brain.observation_running,
                "health_check_ok": self.brain.health_check_ok,
                "error_count": self.brain.error_count,
            },
            "mission": {
                "active_missions": self.mission.active_missions,
                "completed_missions": self.mission.completed_missions,
                "failed_missions": self.mission.failed_missions,
                "stalled_missions": self.mission.stalled_missions,
            },
            "scheduler": {
                "tasks_queued": self.scheduler.tasks_queued,
                "tasks_running": self.scheduler.tasks_running,
                "tasks_completed": self.scheduler.tasks_completed,
                "overloaded": self.scheduler.overloaded,
            },
            "provider": {
                "active_providers": self.provider.active_providers,
                "healthy_providers": self.provider.healthy_providers,
                "degraded_providers": self.provider.degraded_providers,
            },
            "timestamp": self.timestamp,
        }


# ── GuardianSupervisor ────────────────────────────────────────────────────

class GuardianSupervisor:
    """
    Supervisor untuk Guardian Runtime.
    Menerima snapshot dan menyusun laporan status menyeluruh.
    Read-only — tidak mengeksekusi apapun.
    """

    def __init__(self) -> None:
        self._snapshots: List[GuardianSupervisorSnapshot] = []
        self._max_snapshots: int = 50

    def collect(
        self,
        reasoning: Optional[ReasoningStatus] = None,
        decision: Optional[DecisionStatus] = None,
        brain: Optional[BrainStatus] = None,
        mission: Optional[MissionStatus] = None,
        scheduler: Optional[SchedulerStatus] = None,
        provider: Optional[ProviderStatus] = None,
    ) -> GuardianSupervisorSnapshot:
        snapshot = GuardianSupervisorSnapshot(
            reasoning=reasoning or ReasoningStatus(),
            decision=decision or DecisionStatus(),
            brain=brain or BrainStatus(),
            mission=mission or MissionStatus(),
            scheduler=scheduler or SchedulerStatus(),
            provider=provider or ProviderStatus(),
            timestamp=datetime.now().isoformat(timespec="seconds"),
        )
        self._snapshots.append(snapshot)
        if len(self._snapshots) > self._max_snapshots:
            self._snapshots = self._snapshots[-self._max_snapshots:]
        return snapshot

    def latest(self) -> Optional[GuardianSupervisorSnapshot]:
        if not self._snapshots:
            return None
        return self._snapshots[-1]

    def history(self, limit: int = 10) -> List[GuardianSupervisorSnapshot]:
        return self._snapshots[-limit:]

    def clear(self) -> None:
        self._snapshots.clear()

    @property
    def snapshot_count(self) -> int:
        return len(self._snapshots)

    @property
    def has_overall_issues(self) -> bool:
        latest = self.latest()
        if not latest:
            return False
        if latest.scheduler.overloaded:
            return True
        if latest.brain.error_count > 5:
            return True
        if latest.mission.stalled_missions > 0:
            return True
        if latest.provider.degraded_providers > 0:
            return True
        if latest.decision.pending_approvals > 10:
            return True
        return False
