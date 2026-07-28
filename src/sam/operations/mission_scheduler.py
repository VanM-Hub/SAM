"""
OP-127 — Concurrent Mission.

MissionScheduler — single-process scheduler.
Queue, pause, resume, cancel, priority-based, lock checking.

Bukan distributed scheduler. Cukup untuk single process.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Callable, Dict, Any
from datetime import datetime
from enum import Enum

from sam.operations.mission_priority import MissionPriority, PriorityQueue
from sam.operations.workspace_lock import WorkspaceLockManager


class SchedulerState(Enum):
    RUNNING = "RUNNING"
    PAUSED = "PAUSED"
    STOPPED = "STOPPED"


@dataclass
class ScheduledMission:
    """Mission dalam scheduler."""
    mission_id: str
    priority: MissionPriority
    status: str = "pending"           # pending, running, paused, completed, failed, cancelled
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    resources: List[str] = field(default_factory=list)  # resources to lock
    error: str = ""

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "priority": self.priority.label,
            "status": self.status,
            "resources": list(self.resources),
        }

    def to_summary(self) -> str:
        return "{}: {} [{}] ({})".format(
            self.mission_id, self.status, self.priority.label,
            ", ".join(self.resources) if self.resources else "no resources")


class MissionScheduler:
    """Single-process scheduler untuk mission.

    Method:
      submit(mission_id, priority, resources) -> bool
      run_once() -> Optional[str]  # jalankan satu mission, return mission_id
      pause(mission_id) -> bool
      resume(mission_id) -> bool
      cancel(mission_id) -> bool
      get_status(mission_id) -> Optional[dict]
      list_scheduled() -> List[ScheduledMission]
      list_running() -> List[ScheduledMission]
      get_stats() -> dict
    """

    def __init__(self):
        self._queue = PriorityQueue()
        self._missions: Dict[str, ScheduledMission] = {}
        self._running: Dict[str, ScheduledMission] = {}
        self._state = SchedulerState.RUNNING
        self._locks = WorkspaceLockManager()
        self._completed: List[str] = []

    # --- SUBMIT ---

    def submit(self, mission_id: str,
               priority: MissionPriority = MissionPriority.NORMAL,
               resources: Optional[List[str]] = None,
               unique: bool = False) -> bool:
        """Submit mission ke scheduler."""
        if mission_id in self._missions:
            return False

        m = ScheduledMission(
            mission_id=mission_id,
            priority=priority,
            resources=resources or [],
        )
        self._missions[mission_id] = m
        self._queue.enqueue(mission_id, priority, unique=True)
        return True

    # --- RUN ---

    def run_once(self) -> Optional[str]:
        """Jalankan satu mission dari queue.

        Returns:
          mission_id jika ada yang dijalankan, None jika queue kosong.
        """
        if self._state != SchedulerState.RUNNING:
            return None

        mission = self._queue.dequeue()
        if mission is None:
            return None

        mid = mission.mission_id
        sm = self._missions.get(mid)
        if sm is None:
            return None

        # Cek lock untuk semua resources
        can_run = True
        for res in sm.resources:
            if not self._locks.acquire(res, mid, reason="Running: {}".format(mid)):
                can_run = False
                break

        if not can_run:
            # Release partial locks
            self._locks.release_all(mid)
            # Kembalikan ke queue
            # TODO: backoff logic
            self._queue.enqueue(mid, mission.priority, unique=True)
            return None

        sm.status = "running"
        sm.started_at = datetime.now().isoformat()
        self._running[mid] = sm
        return mid

    # --- PAUSE / RESUME / CANCEL ---

    def pause(self, mission_id: str) -> bool:
        """Pause mission."""
        sm = self._missions.get(mission_id)
        if sm is None:
            return False
        if sm.status != "running":
            return False
        sm.status = "paused"
        if mission_id in self._running:
            del self._running[mission_id]
        return True

    def resume(self, mission_id: str) -> bool:
        """Resume mission. Masukkan kembali ke queue."""
        sm = self._missions.get(mission_id)
        if sm is None:
            return False
        if sm.status != "paused":
            return False
        sm.status = "pending"
        self._queue.enqueue(mission_id, sm.priority, unique=True)
        return True

    def cancel(self, mission_id: str) -> bool:
        """Cancel mission."""
        sm = self._missions.get(mission_id)
        if sm is None:
            return False
        if sm.status in ("completed", "failed", "cancelled"):
            return False

        sm.status = "cancelled"
        if mission_id in self._running:
            del self._running[mission_id]
        self._locks.release_all(mission_id)
        self._queue.remove(mission_id)
        return True

    # --- MARK AS COMPLETE/FAILED ---

    def complete(self, mission_id: str, error: str = "") -> bool:
        """Tandai mission selesai."""
        sm = self._missions.get(mission_id)
        if sm is None:
            return False
        sm.status = "failed" if error else "completed"
        sm.completed_at = datetime.now().isoformat()
        sm.error = error
        if mission_id in self._running:
            del self._running[mission_id]
        self._locks.release_all(mission_id)
        self._completed.append(mission_id)
        return True

    # --- QUERIES ---

    def get_status(self, mission_id: str) -> Optional[dict]:
        sm = self._missions.get(mission_id)
        if sm is None:
            return None
        return sm.to_dict()

    def list_scheduled(self) -> List[ScheduledMission]:
        return [m for m in self._missions.values()
                if m.status in ("pending", "paused")]

    def list_running(self) -> List[ScheduledMission]:
        return list(self._running.values())

    def list_completed(self) -> List[ScheduledMission]:
        return [m for m in self._missions.values()
                if m.status in ("completed", "failed")]

    def get_stats(self) -> dict:
        total = len(self._missions)
        running = len(self._running)
        pending = sum(1 for m in self._missions.values() if m.status == "pending")
        paused_count = sum(1 for m in self._missions.values() if m.status == "paused")
        failed = sum(1 for m in self._missions.values() if m.status == "failed")
        completed = sum(1 for m in self._missions.values() if m.status == "completed")
        cancelled = sum(1 for m in self._missions.values() if m.status == "cancelled")
        return {
            "total": total,
            "running": running,
            "pending": pending,
            "paused": paused_count,
            "completed": completed,
            "failed": failed,
            "cancelled": cancelled,
            "state": self._state.value,
            "active_locks": self._locks.active_count,
        }

    # --- SCHEDULER CONTROL ---

    def scheduler_start(self) -> bool:
        if self._state == SchedulerState.RUNNING:
            return True
        self._state = SchedulerState.RUNNING
        return True

    def scheduler_pause(self) -> bool:
        if self._state == SchedulerState.PAUSED:
            return True
        self._state = SchedulerState.PAUSED
        return True

    def scheduler_stop(self) -> bool:
        self._state = SchedulerState.STOPPED
        return True

    @property
    def state(self) -> SchedulerState:
        return self._state

    def reset(self):
        self._queue.reset()
        self._missions.clear()
        self._running.clear()
        self._locks.reset()
        self._completed.clear()
        self._state = SchedulerState.RUNNING
