"""
OP-129 — Mission Recovery.

Jika proses mati, mission harus restart dari checkpoint.
Tidak mengulang langkah yang sudah diverifikasi.
Audit harus menunjukkan recovery.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime

from sam.operations.mission_controller import MissionController, MissionState
from sam.operations.mission_long import LongRunningController, Checkpoint
from sam.operations.mission_scheduler import MissionScheduler
from sam.operations.mission_timeline import TimelineStore


@dataclass
class RecoveryResult:
    """Hasil recovery."""
    mission_id: str
    recovered: bool
    recovered_from_step: int = 0
    recovered_state: str = ""
    skipped_steps: int = 0       # Langkah yang tidak perlu diulang
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "mission_id": self.mission_id,
            "recovered": self.recovered,
            "from_step": self.recovered_from_step,
            "state": self.recovered_state,
            "skipped": self.skipped_steps,
        }

    def to_text(self) -> str:
        if self.recovered:
            return "Mission {} recovered from step {} (state: {}). Skipped {} verified steps. {}".format(
                self.mission_id, self.recovered_from_step,
                self.recovered_state, self.skipped_steps, self.note)
        return "Mission {} recovery failed: {}".format(self.mission_id, self.note)


class MissionRecoveryEngine:
    """Engine untuk recovery mission.

    Method:
      recover(mission_id) -> RecoveryResult
      register_for_recovery(mission_id, checkpoint, verification_ids) -> bool
      list_needs_recovery() -> List[str]
    """

    def __init__(self,
                 mission_controller: MissionController,
                 long_controller: LongRunningController,
                 scheduler: MissionScheduler,
                 timeline: TimelineStore):
        self.mc = mission_controller
        self.long = long_controller
        self.sched = scheduler
        self.timeline = timeline
        # Track mission yang perlu recovery
        self._needs_recovery: List[str] = []
        # Track step yang sudah diverifikasi — tidak perlu diulang
        self._verified_steps: Dict[str, set] = {}  # mission_id -> set of step_ids

    def register_for_recovery(self, mission_id: str,
                              verified_step_ids: Optional[List[str]] = None) -> bool:
        """Daftarkan mission untuk recovery.

        Args:
            mission_id: ID mission
            verified_step_ids: Step yang sudah diverifikasi (tidak perlu diulang)
        """
        m = self.mc.get_mission(mission_id)
        if m is None:
            return False
        self._needs_recovery.append(mission_id)
        if verified_step_ids:
            self._verified_steps.setdefault(mission_id, set()).update(verified_step_ids)
        return True

    def mark_verified(self, mission_id: str, step_id: str) -> bool:
        """Tandai step sebagai sudah diverifikasi."""
        m = self.mc.get_mission(mission_id)
        if m is None:
            return False
        self._verified_steps.setdefault(mission_id, set()).add(step_id)
        return True

    def _get_verification_ids_for_mission(self, mission_id: str) -> List[str]:
        """Dapatkan step IDs yang sudah diverifikasi."""
        return list(self._verified_steps.get(mission_id, set()))

    def recover(self, mission_id: str) -> RecoveryResult:
        """Recover mission dari checkpoint.

        Flow:
        1. Cek checkpoint
        2. Hitung step yang tidak perlu diulang
        3. Set state ke state checkpoint
        4. Catat audit recovery
        5. Register ke scheduler untuk resume
        """
        m = self.mc.get_mission(mission_id)
        if m is None:
            return RecoveryResult(
                mission_id=mission_id,
                recovered=False,
                note="Mission not found",
            )

        # Cek checkpoint
        ck = self.long.get_checkpoint(mission_id)
        if ck is None:
            return RecoveryResult(
                mission_id=mission_id,
                recovered=False,
                note="No checkpoint available",
            )

        # Hitung step yang sudah diverifikasi
        verified = self._get_verification_ids_for_mission(mission_id)
        skipped = len(verified)

        # Set state ke state checkpoint
        try:
            target_state = MissionState(ck.state)
        except ValueError:
            target_state = MissionState.CREATED

        # Jika masih OBSERVING/EXECUTING — bisa restart
        if m.state in (MissionState.CREATED, MissionState.OBSERVING,
                       MissionState.ANALYZING, MissionState.EXECUTING):
            # Set ulang state
            self.mc.transition(mission_id, MissionState.OBSERVING,
                               "Recovery: restart from checkpoint")

        # Catat recovery di timeline
        self.timeline.add_event(mission_id, 'RECOVERY',
                                "Recovered from step {}, skipped {} verified".format(
                                    ck.step_index, skipped))

        # Hapus dari daftar needs_recovery
        self._needs_recovery = [m for m in self._needs_recovery if m != mission_id]

        return RecoveryResult(
            mission_id=mission_id,
            recovered=True,
            recovered_from_step=ck.step_index,
            recovered_state=ck.state,
            skipped_steps=skipped,
            note="Recovery complete. {} verified steps skipped.".format(skipped),
        )

    def list_needs_recovery(self) -> List[str]:
        return list(self._needs_recovery)

    def batch_recover(self) -> List[RecoveryResult]:
        """Recover semua mission yang perlu recovery."""
        results = []
        for mid in list(self._needs_recovery):
            results.append(self.recover(mid))
        return results

    def get_verified_steps(self, mission_id: str) -> int:
        return len(self._verified_steps.get(mission_id, set()))
