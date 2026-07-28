"""
OP-121 — Mission Controller.

Orkestrator lifecycle misi. BUKAN pengganti Conversation.
MissionController hanya mengatur state mission.
Tidak ada business logic di sini.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class MissionState(Enum):
    """State mission. Immutable setelah dibuat."""
    CREATED = "CREATED"
    OBSERVING = "OBSERVING"
    ANALYZING = "ANALYZING"
    WAITING_APPROVAL = "WAITING_APPROVAL"
    EXECUTING = "EXECUTING"
    VERIFYING = "VERIFYING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


# Valid transitions: {from_state: [to_state, ...]}
MISSION_TRANSITIONS: Dict[MissionState, List[MissionState]] = {
    MissionState.CREATED: [MissionState.OBSERVING, MissionState.CANCELLED],
    MissionState.OBSERVING: [MissionState.ANALYZING, MissionState.FAILED, MissionState.CANCELLED],
    MissionState.ANALYZING: [MissionState.WAITING_APPROVAL, MissionState.OBSERVING, MissionState.FAILED, MissionState.CANCELLED],
    MissionState.WAITING_APPROVAL: [MissionState.EXECUTING, MissionState.ANALYZING, MissionState.CANCELLED, MissionState.FAILED],
    MissionState.EXECUTING: [MissionState.VERIFYING, MissionState.ANALYZING, MissionState.FAILED, MissionState.CANCELLED],
    MissionState.VERIFYING: [MissionState.OBSERVING, MissionState.COMPLETED, MissionState.FAILED, MissionState.CANCELLED],
    MissionState.COMPLETED: [],  # terminal
    MissionState.FAILED: [],     # terminal
    MissionState.CANCELLED: [],  # terminal
}


@dataclass
class MissionStateEntry:
    """Satu entry perubahan state. Append-only."""
    from_state: MissionState
    to_state: MissionState
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    reason: str = ""

    def to_dict(self) -> dict:
        return {
            "from": self.from_state.value,
            "to": self.to_state.value,
            "timestamp": self.timestamp,
            "reason": self.reason,
        }


@dataclass
class Mission:
    """Mission aggregate. State mutability terbatas.

    Mission hanya menyimpan state dan metadata.
    Business logic ada di MissionController.
    """

    mission_id: str
    name: str
    state: MissionState = MissionState.CREATED
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    state_history: List[MissionStateEntry] = field(default_factory=list)
    tags: Dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "name": self.name,
            "state": self.state.value,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "tags": dict(self.tags),
        }

    def to_summary(self) -> str:
        return "Mission {}: {} — State: {}".format(
            self.mission_id, self.name, self.state.value)


class MissionController:
    """Orkestrator mission.

    Method:
      create_mission(mission_id, name) -> Mission
      transition(mission_id, new_state) -> bool
      get_mission(mission_id) -> Optional[Mission]
      list_missions(state_filter=None) -> List[Mission]
      count_by_state() -> dict
    """

    def __init__(self):
        self._missions: Dict[str, Mission] = {}

    # --- CORE ---

    def create_mission(self, mission_id: str, name: str,
                       tags: Optional[Dict[str, str]] = None) -> Mission:
        """Buat mission baru. State awal: CREATED."""
        if mission_id in self._missions:
            raise ValueError("Mission {} already exists".format(mission_id))
        m = Mission(
            mission_id=mission_id,
            name=name,
            tags=tags or {},
        )
        self._missions[mission_id] = m
        return m

    def transition(self, mission_id: str, new_state: MissionState,
                   reason: str = "") -> bool:
        """Transisi state mission.

        Validasi transisi. Append state_history.
        Terminal states (COMPLETED/FAILED/CANCELLED) tidak bisa dipindah.
        """
        m = self._get(mission_id)
        if m is None:
            raise ValueError("Mission {} not found".format(mission_id))

        if m.state == new_state:
            return True  # no-op

        allowed = MISSION_TRANSITIONS.get(m.state, [])
        if new_state not in allowed:
            return False

        entry = MissionStateEntry(
            from_state=m.state,
            to_state=new_state,
            reason=reason,
        )
        m.state_history.append(entry)
        m.state = new_state
        m.updated_at = datetime.now().isoformat()
        return True

    def get_state(self, mission_id: str) -> Optional[MissionState]:
        """Dapatkan state mission."""
        m = self._get(mission_id)
        return m.state if m else None

    def is_terminal(self, mission_id: str) -> bool:
        """Cek apakah mission sudah terminal."""
        m = self._get(mission_id)
        if m is None:
            return False
        return m.state in (MissionState.COMPLETED,
                           MissionState.FAILED,
                           MissionState.CANCELLED)

    # --- QUERY ---

    def _get(self, mission_id: str) -> Optional[Mission]:
        return self._missions.get(mission_id)

    def get_mission(self, mission_id: str) -> Optional[Mission]:
        """Dapatkan mission lengkap."""
        return self._get(mission_id)

    def list_missions(self, state_filter: Optional[MissionState] = None) -> List[Mission]:
        """List mission. Optional filter state."""
        if state_filter is None:
            return list(self._missions.values())
        return [m for m in self._missions.values() if m.state == state_filter]

    def count_by_state(self) -> Dict[str, int]:
        """Hitung mission per state. Untuk dashboard."""
        counts: Dict[str, int] = {s.value: 0 for s in MissionState}
        for m in self._missions.values():
            counts[m.state.value] += 1
        return counts

    def delete_mission(self, mission_id: str) -> bool:
        """Hapus mission (hanya jika terminal)."""
        m = self._get(mission_id)
        if m is None:
            return False
        if not self.is_terminal(mission_id):
            return False
        del self._missions[mission_id]
        return True

    # --- BULK ---

    def reset(self):
        """Hapus semua mission."""
        self._missions.clear()
