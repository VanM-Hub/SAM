"""Widgets — Immutable widget models for presentation layer.

All widgets are frozen dataclasses. No renderer. No business logic.
"""

from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional
from datetime import datetime


@dataclass(frozen=True)
class MissionWidget:
    """Single mission status widget."""
    mission_id: str = ""
    mission_name: str = ""
    state: str = "pending"
    progress_pct: float = 0.0
    current_step: str = ""
    steps_total: int = 0
    steps_done: int = 0
    risk: str = "low"
    started_at: str = ""
    remaining_time: str = ""


@dataclass(frozen=True)
class MissionWidgetCollection:
    """Collection of mission widgets."""
    items: tuple[MissionWidget, ...] = field(default_factory=tuple)
    total: int = 0
    running: int = 0
    failed: int = 0
    completed: int = 0


@dataclass(frozen=True)
class ApprovalWidget:
    """Single approval request widget."""
    approval_id: str = ""
    title: str = ""
    action: str = ""
    risk: str = "low"
    submitted_at: str = ""
    expires_at: str = ""
    reason: str = ""


@dataclass(frozen=True)
class ApprovalWidgetCollection:
    """Collection of approval widgets."""
    items: tuple[ApprovalWidget, ...] = field(default_factory=tuple)
    total: int = 0
    urgent: int = 0


@dataclass(frozen=True)
class NotificationWidget:
    """Single notification widget."""
    type_id: str = ""
    title: str = ""
    severity: str = "information"
    source_kind: str = ""
    created_at: str = ""
    acknowledged: bool = False


@dataclass(frozen=True)
class NotificationWidgetCollection:
    """Collection of notification widgets."""
    items: tuple[NotificationWidget, ...] = field(default_factory=tuple)
    total: int = 0
    unread: int = 0
    critical: int = 0


@dataclass(frozen=True)
class TimelineEvent:
    """Single timeline event widget."""
    event_id: str = ""
    event_type: str = ""
    title: str = ""
    timestamp: str = ""
    severity: str = "information"


@dataclass(frozen=True)
class TimelineWidgetCollection:
    """Collection of timeline events."""
    items: tuple[TimelineEvent, ...] = field(default_factory=tuple)
    total: int = 0
    latest: Optional[str] = None


@dataclass(frozen=True)
class TrustWidget:
    """Trust score display widget."""
    score: float = 0.0
    grade: str = "B"
    total_decisions: int = 0
    history: tuple[float, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class HealthWidget:
    """System health widget."""
    status: str = "unknown"
    score: float = 0.0
    warnings: tuple[str, ...] = field(default_factory=tuple)
    components: tuple[tuple[str, str], ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class WorkspaceWidget:
    """Workspace lock status widget."""
    total_locks: int = 0
    active_locks: int = 0
    lock_holders: tuple[str, ...] = field(default_factory=tuple)


@dataclass(frozen=True)
class SchedulerWidget:
    """Scheduler status widget."""
    queue_size: int = 0
    running_count: int = 0
    next_scheduled: Optional[str] = None


@dataclass(frozen=True)
class SummaryWidget:
    """Summary display widget."""
    title: str = ""
    verdict: str = ""
    details: str = ""
    trust_grade: str = ""
    duration: str = ""
    steps: str = ""


@dataclass(frozen=True)
class WidgetRegistry:
    """Registry of all active widgets on screen."""
    mission: Optional[MissionWidgetCollection] = None
    approval: Optional[ApprovalWidgetCollection] = None
    notification: Optional[NotificationWidgetCollection] = None
    timeline: Optional[TimelineWidgetCollection] = None
    trust: Optional[TrustWidget] = None
    health: Optional[HealthWidget] = None
    workspace: Optional[WorkspaceWidget] = None
    scheduler: Optional[SchedulerWidget] = None
    summary: Optional[SummaryWidget] = None

    @property
    def widget_count(self) -> int:
        count = 0
        for w in (self.mission, self.approval, self.notification,
                   self.timeline, self.trust, self.health,
                   self.workspace, self.scheduler, self.summary):
            if w is not None:
                count += 1
        return count
