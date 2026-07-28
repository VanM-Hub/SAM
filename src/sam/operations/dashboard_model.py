"""
MissionDashboardDTO — Pure DTO for operational dashboard view.

No renderer. Complete snapshot of mission/health/trust state.
Ready for any frontend (CLI, GUI, Conversation).
"""

from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


# ── Sub-models ────────────────────────────────────────────────────────

@dataclass
class MissionStatSummary:
    total: int = 0
    pending: int = 0
    running: int = 0
    completed: int = 0
    failed: int = 0


@dataclass
class HealthSummary:
    overall: str = "unknown"  # "healthy" | "degraded" | "unhealthy"
    score: float = 0.0
    warnings: list[str] = field(default_factory=list)


@dataclass
class TrustSummary:
    current_score: float = 0.0
    current_grade: str = ""
    total_decisions: int = 0


@dataclass
class SchedulerStatus:
    queue_size: int = 0
    running_count: int = 0
    next_scheduled: Optional[str] = None


@dataclass
class WorkspaceLockStatus:
    total_locks: int = 0
    active_locks: int = 0
    held_by: list[str] = field(default_factory=list)


@dataclass
class TimelineSnapshot:
    latest_events: list[dict] = field(default_factory=list)
    today_event_count: int = 0


@dataclass
class RecentActivity:
    decisions: list[dict] = field(default_factory=list)
    approvals: list[dict] = field(default_factory=list)
    recoveries: list[dict] = field(default_factory=list)
    alerts: list[dict] = field(default_factory=list)


# ── Root DTO ──────────────────────────────────────────────────────────

@dataclass
class MissionDashboardDTO:
    """Complete operational dashboard — one DTO, all data."""

    # ── Sections ──────────────────────────────────────────────────────
    mission_stats: MissionStatSummary = field(default_factory=MissionStatSummary)
    health: HealthSummary = field(default_factory=HealthSummary)
    trust: TrustSummary = field(default_factory=TrustSummary)
    scheduler: SchedulerStatus = field(default_factory=SchedulerStatus)
    workspace_locks: WorkspaceLockStatus = field(default_factory=WorkspaceLockStatus)
    timeline: TimelineSnapshot = field(default_factory=TimelineSnapshot)
    recent_activity: RecentActivity = field(default_factory=RecentActivity)

    # ── Metadata ──────────────────────────────────────────────────────
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def is_healthy(self) -> bool:
        return self.health.overall == "healthy"

    @property
    def summary_line(self) -> str:
        return (
            f"{self.mission_stats.running} running, "
            f"{self.mission_stats.failed} failed, "
            f"health={self.health.overall}, "
            f"trust={self.trust.current_grade}"
        )


# ── Builder ───────────────────────────────────────────────────────────

class MissionDashboardBuilder:
    """Populates MissionDashboardDTO from operational repositories."""

    def __init__(self) -> None:
        pass

    def build(self) -> MissionDashboardDTO:
        dto = MissionDashboardDTO()
        self._populate_mission_stats(dto)
        self._populate_health(dto)
        self._populate_trust(dto)
        self._populate_scheduler(dto)
        self._populate_workspace_locks(dto)
        self._populate_timeline(dto)
        self._populate_recent_activity(dto)
        return dto

    # ── Stubs — each delegates to the respective repository ──────────

    def _populate_mission_stats(self, dto: MissionDashboardDTO) -> None:
        """Read from mission_repo."""
        pass

    def _populate_health(self, dto: MissionDashboardDTO) -> None:
        """Read from health monitor / telemetry."""
        pass

    def _populate_trust(self, dto: MissionDashboardDTO) -> None:
        """Read from trust_repo."""
        pass

    def _populate_scheduler(self, dto: MissionDashboardDTO) -> None:
        """Read from mission_scheduler."""
        pass

    def _populate_workspace_locks(self, dto: MissionDashboardDTO) -> None:
        """Read from workspace_lock / lock_repo."""
        pass

    def _populate_timeline(self, dto: MissionDashboardDTO) -> None:
        """Read from timeline_store."""
        pass

    def _populate_recent_activity(self, dto: MissionDashboardDTO) -> None:
        """Read from decision_repo, approval_repo, audit_repo."""
        pass
