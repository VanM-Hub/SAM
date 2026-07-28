"""
OP-122 — Multi-step Mission.

Satu mission bisa memiliki banyak DecisionProposal.
MissionStepTracker melacak langkah mana yang aktif.
Step bisa sukses, gagal, atau branching (misal: masih penuh → langkah berbeda).
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum


class StepStatus(Enum):
    PENDING = "PENDING"
    ACTIVE = "ACTIVE"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"


@dataclass
class MissionStep:
    """Satu langkah dalam multi-step mission.

    Tidak berisi business logic. Hanya metadata dan status.
    DecisionProposal dibuat dan di-track oleh Conversation.
    """
    step_id: str
    decision_id: str           # ID keputusan yang dihasilkan
    description: str            # "Clean cache", "Delete temp files"
    status: StepStatus = StepStatus.PENDING
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "decision_id": self.decision_id,
            "description": self.description,
            "status": self.status.value,
        }

    def to_summary(self) -> str:
        return "  [{}] {} — {}".format(
            self.status.value, self.step_id, self.description)


@dataclass
class MultiStepMission:
    """Multi-step mission.

    Menyimpan:
    - Daftar step
    - Step aktif saat ini
    - Alasan berhenti jika mission pause/stop di tengah
    """
    mission_id: str
    steps: List[MissionStep] = field(default_factory=list)
    current_step_index: int = 0
    stop_reason: str = ""
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())

    @property
    def current_step(self) -> Optional[MissionStep]:
        """Step yang sedang aktif."""
        if self.current_step_index < len(self.steps):
            return self.steps[self.current_step_index]
        return None

    @property
    def is_complete(self) -> bool:
        """Semua step sudah selesai (success/skipped) atau stop."""
        if self.stop_reason:
            return True
        return all(s.status in (StepStatus.SUCCESS,
                                StepStatus.FAILED,
                                StepStatus.SKIPPED)
                   for s in self.steps)

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "current_step_index": self.current_step_index,
            "total_steps": len(self.steps),
            "is_complete": self.is_complete,
            "stop_reason": self.stop_reason,
            "steps": [s.to_dict() for s in self.steps],
        }

    def to_text(self) -> str:
        lines = []
        lines.append("Multi-step mission: {}".format(self.mission_id))
        lines.append("  Active step: {} ({}/{})".format(
            self.current_step.step_id if self.current_step else "DONE",
            self.current_step_index + 1 if self.current_step else len(self.steps),
            len(self.steps)))
        if self.stop_reason:
            lines.append("  Stopped: {}".format(self.stop_reason))
        for s in self.steps:
            lines.append(s.to_summary())
        return "\n".join(lines)


class MissionStepController:
    """Controller untuk multi-step mission.

    Method:
      start_mission(mission_id) — aktifkan step pertama
      next_step(mission_id, status, detail) — lanjut ke step berikutnya
      stop(mission_id, reason) — hentikan mission di tengah
      resume(mission_id) — lanjutkan mission yang distop
      get_step(mission_id, step_id) — detail step
    """

    def __init__(self):
        self._missions: Dict[str, MultiStepMission] = {}

    def register(self, mission: MultiStepMission):
        """Daftarkan multi-step mission."""
        self._missions[mission.mission_id] = mission

    def _get(self, mission_id: str) -> Optional[MultiStepMission]:
        return self._missions.get(mission_id)

    def start_mission(self, mission_id: str) -> bool:
        """Aktifkan step pertama. Hanya jika ada step."""
        m = self._get(mission_id)
        if m is None:
            return False
        if not m.steps:
            return False
        if m.stop_reason:
            return False  # sudah distop, gunakan resume
        m.steps[0].status = StepStatus.ACTIVE
        return True

    def next_step(self, mission_id: str, status: StepStatus,
                  detail: str = "") -> bool:
        """Selesaikan step aktif dan lanjut ke step berikutnya.

        Args:
            mission_id: ID mission
            status: SUCCESS, FAILED, atau SKIPPED
            detail: Alasan (misal: "disk still full, need next step")
        Returns:
            True jika ada step berikutnya, False jika mission selesai
        """
        m = self._get(mission_id)
        if m is None:
            return False
        if m.stop_reason:
            return False
        if m.current_step is None:
            return False  # sudah di akhir

        # Update step aktif
        m.current_step.status = status

        # Jika FAILED dan ada stop_reason — mission berhenti
        if status == StepStatus.FAILED:
            if detail:
                m.stop_reason = detail
            return False

        # Skip ke step berikutnya
        m.current_step_index += 1
        next_step = m.current_step
        if next_step:
            next_step.status = StepStatus.ACTIVE
            return True
        else:
            return False  # mission complete

    def stop(self, mission_id: str, reason: str) -> bool:
        """Hentikan mission di tengah."""
        m = self._get(mission_id)
        if m is None:
            return False
        if m.is_complete:
            return False  # sudah selesai
        m.stop_reason = reason
        if m.current_step:
            m.current_step.status = StepStatus.SKIPPED
        return True

    def resume(self, mission_id: str) -> bool:
        """Lanjutkan mission yang distop."""
        m = self._get(mission_id)
        if m is None:
            return False
        if not m.stop_reason:
            return False  # tidak distop
        m.stop_reason = ""
        # Aktifkan step yang belum selesai
        current = m.current_step
        if current and current.status == StepStatus.SKIPPED:
            current.status = StepStatus.ACTIVE
        elif current is None:
            # Semua step sudah selesai
            return False
        return True

    def get_mission(self, mission_id: str) -> Optional[MultiStepMission]:
        return self._get(mission_id)

    def list_missions(self) -> List[MultiStepMission]:
        return list(self._missions.values())

    def reset(self):
        self._missions.clear()
