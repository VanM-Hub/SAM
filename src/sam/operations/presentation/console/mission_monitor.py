"""MissionMonitor — Runtime mission monitoring for the SAM Console.

Displays active missions, progress, waiting reasons, verification state,
and recovery state. Pure view-model composition using existing DTOs.
No business logic. No storage access.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional, Tuple
from datetime import datetime


@dataclass(frozen=True)
class MissionEntry:
    """A single mission in the monitor view (immutable, from DTO data)."""
    mission_id: str
    name: str
    status: str  # running, pending, completed, failed, paused
    progress: float  # 0.0 - 1.0
    goal: str
    condition: str
    waiting_reason: str = ""
    strategy: str = "default"
    verification_state: str = "unknown"
    recovery_state: str = "none"
    started_at: str = ""
    estimated_end: str = ""
    steps: int = 0
    completed_steps: int = 0
    confidence: float = 0.0


@dataclass(frozen=True)
class MissionMonitor:
    """Mission monitoring view model.

    Composed from mission DTO data. All fields are read-only.
    """

    missions: Tuple[MissionEntry, ...] = ()
    total: int = 0
    running: int = 0
    pending: int = 0
    completed: int = 0
    failed: int = 0
    paused: int = 0
    filtered_count: int = 0

    # ── Filtering ───────────────────────────────────────────────────

    def by_status(self, status: str) -> MissionMonitor:
        """Filter missions by status. Returns new instance."""
        if status == "all":
            return self
        filtered = tuple(m for m in self.missions if m.status == status)
        return MissionMonitor(
            missions=filtered,
            total=self.total,
            running=sum(1 for m in filtered if m.status == "running"),
            pending=sum(1 for m in filtered if m.status == "pending"),
            completed=sum(1 for m in filtered if m.status == "completed"),
            failed=sum(1 for m in filtered if m.status == "failed"),
            paused=sum(1 for m in filtered if m.status == "paused"),
            filtered_count=len(filtered),
        )

    def search(self, query: str) -> MissionMonitor:
        """Filter missions by name/id keyword. Returns new instance."""
        q = query.lower()
        if not q:
            return self
        filtered = tuple(
            m for m in self.missions
            if q in m.name.lower() or q in m.mission_id.lower()
        )
        return MissionMonitor(
            missions=filtered,
            total=self.total,
            running=sum(1 for m in filtered if m.status == "running"),
            pending=sum(1 for m in filtered if m.status == "pending"),
            completed=sum(1 for m in filtered if m.status == "completed"),
            failed=sum(1 for m in filtered if m.status == "failed"),
            paused=sum(1 for m in filtered if m.status == "paused"),
            filtered_count=len(filtered),
        )

    def sort_by(self, key: str = "newest") -> MissionMonitor:
        """Sort missions. Returns new instance."""
        if key == "name":
            sorted_m = tuple(
                sorted(self.missions, key=lambda m: m.name)
            )
        elif key == "status":
            order = {"running": 0, "pending": 1, "paused": 2,
                     "completed": 3, "failed": 4}
            sorted_m = tuple(
                sorted(self.missions,
                       key=lambda m: order.get(m.status, 99))
            )
        elif key == "oldest":
            sorted_m = tuple(
                sorted(self.missions, key=lambda m: m.started_at)
            )
        else:  # newest (default)
            sorted_m = tuple(
                sorted(self.missions, key=lambda m: m.started_at,
                       reverse=True)
            )
        return MissionMonitor(
            missions=sorted_m,
            total=self.total,
            running=self.running, pending=self.pending,
            completed=self.completed, failed=self.failed,
            paused=self.paused, filtered_count=self.filtered_count,
        )

    @property
    def active_count(self) -> int:
        return self.running + self.pending

    @property
    def summary_line(self) -> str:
        return (
            f"Missions: {self.total} total, {self.running} running, "
            f"{self.pending} pending, {self.completed} completed, "
            f"{self.failed} failed"
        )


# ── Factory ───────────────────────────────────────────────────────────

@dataclass(frozen=True)
class MissionMonitorFactory:
    """Creates MissionMonitor from raw mission data.

    This is the ONLY place that translates domain DTO fields
    into MissionEntry fields. All other code consumes MissionMonitor.
    """

    @staticmethod
    def from_dashboard(dashboard: object) -> MissionMonitor:
        """Build MissionMonitor from a ConsoleDashboard DTO.

        Uses fields: total_missions, running_missions, pending_missions,
        failed_missions, completed_missions.
        """
        if dashboard is None:
            return MissionMonitor()

        return MissionMonitor(
            total=getattr(dashboard, 'total_missions', 0),
            running=getattr(dashboard, 'running_missions', 0),
            pending=getattr(dashboard, 'pending_missions', 0),
            completed=getattr(dashboard, 'completed_missions', 0),
            failed=getattr(dashboard, 'failed_missions', 0),
        )

    @staticmethod
    def from_mission_list(
        missions: List[dict],
        total: int = 0,
    ) -> MissionMonitor:
        """Build MissionMonitor from a list of mission dicts.

        Each dict should contain keys matching MissionEntry fields.
        """
        entries: List[MissionEntry] = []
        for m in missions:
            entries.append(MissionEntry(
                mission_id=str(m.get('mission_id', m.get('id', ''))),
                name=str(m.get('name', m.get('mission_name', ''))),
                status=str(m.get('status', 'unknown')),
                progress=float(m.get('progress', 0.0)),
                goal=str(m.get('goal', m.get('description', ''))),
                condition=str(m.get('condition', '')),
                waiting_reason=str(m.get('waiting_reason', '')),
                strategy=str(m.get('strategy', 'default')),
                verification_state=str(
                    m.get('verification_state', m.get('verified_reason', 'unknown'))
                ),
                recovery_state=str(m.get('recovery_state', 'none')),
                started_at=str(m.get('started_at', '')),
                estimated_end=str(m.get('estimated_end', '')),
                steps=int(m.get('steps', 0)),
                completed_steps=int(m.get('completed_steps', 0)),
                confidence=float(m.get('confidence', 0.0)),
            ))

        total_count = total or len(entries)
        return MissionMonitor(
            missions=tuple(entries),
            total=total_count,
            running=sum(1 for e in entries if e.status == 'running'),
            pending=sum(1 for e in entries if e.status == 'pending'),
            completed=sum(1 for e in entries if e.status == 'completed'),
            failed=sum(1 for e in entries if e.status == 'failed'),
            paused=sum(1 for e in entries if e.status == 'paused'),
            filtered_count=len(entries),
        )

    @staticmethod
    def empty() -> MissionMonitor:
        return MissionMonitor()
