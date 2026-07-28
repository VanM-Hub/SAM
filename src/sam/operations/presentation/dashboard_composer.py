"""DashboardComposer — Pure compositor for ConsoleDashboard.

Input: MissionDashboardDTO, ActionCenterDTO, NotificationDTO, SummaryDTO
Output: ConsoleDashboard (immutable view model)

No business logic. No queries. No access to storage/repository.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime

from ..dashboard_model import MissionDashboardDTO
from ..action_center import ActionCenterDTO
from ..notification import Notification, NOTIFICATION_SEVERITY
from ..summary_builder import OperationalSummary


@dataclass(frozen=True)
class ConsoleDashboard:
    """Dashboard ready for rendering — pure data composition."""
    title: str = "Operational Dashboard"
    total_missions: int = 0
    running_missions: int = 0
    pending_missions: int = 0
    failed_missions: int = 0
    completed_missions: int = 0
    health_status: str = "unknown"
    health_score: float = 0.0
    health_warnings: int = 0
    trust_score: float = 0.0
    trust_grade: str = ""
    total_decisions: int = 0
    pending_approvals: int = 0
    approval_items: tuple[str, ...] = field(default_factory=tuple)
    unread_notifications: int = 0
    critical_notifications: int = 0
    latest_notification: str = ""
    queue_size: int = 0
    next_scheduled: Optional[str] = None
    latest_mission_summary: str = ""
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass(frozen=True)
class DashboardComposer:
    """Composes ConsoleDashboard from up to 4 DTOs."""

    @staticmethod
    def compose(
        mission_dto: Optional[MissionDashboardDTO] = None,
        action_dto: Optional[ActionCenterDTO] = None,
        notification_store: Optional[list[Notification]] = None,
        summary: Optional[OperationalSummary] = None,
    ) -> ConsoleDashboard:
        total = 0
        running = 0
        pending_m = 0
        failed = 0
        completed = 0

        if mission_dto and mission_dto.mission_stats:
            ms = mission_dto.mission_stats
            total = ms.total
            pending_m = ms.pending
            running = ms.running
            completed = ms.completed
            failed = ms.failed

        health_status = "unknown"
        health_score = 0.0
        health_warnings = 0
        if mission_dto and mission_dto.health:
            health_status = mission_dto.health.overall
            health_score = mission_dto.health.score
            health_warnings = len(mission_dto.health.warnings)

        t_score = 0.0
        t_grade = ""
        t_decisions = 0
        if mission_dto and mission_dto.trust:
            t_score = mission_dto.trust.current_score
            t_grade = mission_dto.trust.current_grade
            t_decisions = mission_dto.trust.total_decisions

        pending_app = 0
        app_titles: list[str] = []
        if action_dto:
            pending_app = action_dto.total_pending
            # Collect titles from all actionable buckets
            all_items = list(action_dto.pending_approvals)
            all_items.extend(action_dto.pending_missions)
            all_items.extend(action_dto.waiting_human)
            app_titles = [
                f"{item.title} ({item.status})"
                for item in all_items
                if item.status == "pending"
            ][:10]

        unread = 0
        critical = 0
        latest = ""
        if notification_store:
            unread = sum(1 for n in notification_store if not n.acknowledged)
            critical = sum(1 for n in notification_store
                          if NOTIFICATION_SEVERITY.get(n.type_id, "") == "critical")
            if notification_store:
                latest = notification_store[-1].title

        qsize = 0
        next_ts: Optional[str] = None
        if mission_dto and mission_dto.scheduler:
            qsize = mission_dto.scheduler.queue_size
            next_ts = mission_dto.scheduler.next_scheduled

        lsummary = ""
        if summary:
            lsummary = summary.short_summary

        return ConsoleDashboard(
            total_missions=total,
            running_missions=running,
            pending_missions=pending_m,
            failed_missions=failed,
            completed_missions=completed,
            health_status=health_status,
            health_score=health_score,
            health_warnings=health_warnings,
            trust_score=t_score,
            trust_grade=t_grade,
            total_decisions=t_decisions,
            pending_approvals=pending_app,
            approval_items=tuple(app_titles),
            unread_notifications=unread,
            critical_notifications=critical,
            latest_notification=latest,
            queue_size=qsize,
            next_scheduled=next_ts,
            latest_mission_summary=lsummary,
        )
