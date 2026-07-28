"""
OP-126 — Mission Priority.

Priority: CRITICAL > HIGH > NORMAL > LOW.
Menentukan approval, execution order, notification, retry behavior.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MissionPriority(Enum):
    CRITICAL = 0   # Tertinggi
    HIGH = 1
    NORMAL = 2
    LOW = 3

    @property
    def label(self) -> str:
        return self.name

    @property
    def requires_human_approval(self) -> bool:
        return self in (MissionPriority.CRITICAL, MissionPriority.HIGH)

    @property
    def auto_retry(self) -> bool:
        """Priority menentukan apakah auto-retry diizinkan."""
        return self in (MissionPriority.CRITICAL, MissionPriority.HIGH)

    @property
    def max_retries(self) -> int:
        if self == MissionPriority.CRITICAL:
            return 5
        elif self == MissionPriority.HIGH:
            return 3
        elif self == MissionPriority.NORMAL:
            return 2
        return 1  # LOW

    @property
    def notification_level(self) -> str:
        if self == MissionPriority.CRITICAL:
            return "immediate"
        elif self == MissionPriority.HIGH:
            return "high"
        elif self == MissionPriority.NORMAL:
            return "normal"
        return "low"


@dataclass
class PrioritizedMission:
    """Mission dengan prioritas."""
    mission_id: str
    priority: MissionPriority
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "priority": self.priority.label,
            "created_at": self.created_at,
        }


class PriorityQueue:
    """Priority queue untuk mission.

    Internal: list of PrioritizedMission, sorted by priority (CRITICAL first).
    Bukan production-grade queue — cukup untuk single-process.

    Method:
      enqueue(mission_id, priority) -> bool
      dequeue() -> Optional[PrioritizedMission]
      peek() -> Optional[PrioritizedMission]
      remove(mission_id) -> bool
      list_pending() -> List[PrioritizedMission]
      list_by_priority(priority) -> List[PrioritizedMission]
      count -> int
    """

    def __init__(self):
        self._missions: List[PrioritizedMission] = []
        self._enqueued_ids: set = set()

    def enqueue(self, mission_id: str, priority: MissionPriority,
                unique: bool = False) -> bool:
        """Masukkan mission ke queue.

        Args:
            mission_id: ID mission
            priority: Prioritas mission
            unique: Jika True, cegah duplikat
        """
        if unique and mission_id in self._enqueued_ids:
            return False
        m = PrioritizedMission(
            mission_id=mission_id,
            priority=priority,
        )
        self._missions.append(m)
        self._enqueued_ids.add(mission_id)
        # Sort: priority value lower = higher priority
        # Bila sama priority, FIFO (stable sort)
        self._missions.sort(key=lambda x: (x.priority.value, x.created_at))
        return True

    def dequeue(self) -> Optional[PrioritizedMission]:
        """Ambil mission dengan prioritas tertinggi."""
        if not self._missions:
            return None
        m = self._missions.pop(0)
        self._enqueued_ids.discard(m.mission_id)
        return m

    def peek(self) -> Optional[PrioritizedMission]:
        """Lihat mission tertinggi tanpa mengeluarkan."""
        if not self._missions:
            return None
        return self._missions[0]

    def remove(self, mission_id: str) -> bool:
        """Hapus mission dari queue."""
        before = len(self._missions)
        self._missions = [m for m in self._missions if m.mission_id != mission_id]
        self._enqueued_ids.discard(mission_id)
        return len(self._missions) < before

    def list_pending(self) -> List[PrioritizedMission]:
        """Semua mission pending."""
        return list(self._missions)

    def list_by_priority(self, priority: MissionPriority) -> List[PrioritizedMission]:
        """Mission dengan priority tertentu."""
        return [m for m in self._missions if m.priority == priority]

    @property
    def count(self) -> int:
        return len(self._missions)

    @property
    def is_empty(self) -> bool:
        return len(self._missions) == 0

    def reset(self):
        self._missions.clear()
        self._enqueued_ids.clear()
