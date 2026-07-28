"""
OP-123 — Long Running Mission.

Mission bisa berjalan berjam-jam.
Checkpoint, restart-safe, elapsed time, retry count, approval history, verification history.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime


@dataclass
class Checkpoint:
    """Snapshot mission di satu titik waktu.

    Cukup untuk restart dari sini.
    Step index, state, timestamp.
    """
    step_index: int
    state: str                  # MissionState value
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    note: str = ""

    def to_dict(self) -> dict:
        return {
            "step_index": self.step_index,
            "state": self.state,
            "timestamp": self.timestamp,
            "note": self.note,
        }


@dataclass
class RetryRecord:
    """Catatan retry untuk satu langkah."""
    step_id: str
    attempt: int
    reason: str
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> dict:
        return {
            "step_id": self.step_id,
            "attempt": self.attempt,
            "reason": self.reason,
            "timestamp": self.timestamp,
        }


@dataclass
class LongRunningMission:
    """Mission yang bisa bertahan dari restart.

    Semua data dalam bentuk immutable records — append-only.

    Fields:
      mission_id: str
      checkpoint: Checkpoint terakhir
      elapsed_seconds: Durasi sejak start
      retry_count: Total retry seluruh mission
      retries: Daftar RetryRecord
      approval_history: Daftar approval
      verification_history: Daftar verification
      started_at: Timestamp start
    """
    mission_id: str
    started_at: str = field(default_factory=lambda: datetime.now().isoformat())
    checkpoint: Optional[Checkpoint] = None
    elapsed_seconds: float = 0.0
    retry_count: int = 0
    retries: List[RetryRecord] = field(default_factory=list)
    approval_history: List[dict] = field(default_factory=list)
    verification_history: List[dict] = field(default_factory=list)

    def to_dict(self) -> dict:
        ck = self.checkpoint.to_dict() if self.checkpoint else None
        return {
            "mission_id": self.mission_id,
            "started_at": self.started_at,
            "checkpoint": ck,
            "elapsed_seconds": self.elapsed_seconds,
            "retry_count": self.retry_count,
            "retries": len(self.retries),
            "approvals": len(self.approval_history),
            "verifications": len(self.verification_history),
        }

    def to_summary(self) -> str:
        ck = self.checkpoint
        ck_info = "Step {} / {}".format(ck.step_index, ck.state) if ck else "No checkpoint"
        return "{}: {} | Elapsed: {:.0f}s | Retries: {} | {}".format(
            self.mission_id, ck_info, self.elapsed_seconds,
            self.retry_count, ck.note if ck else "")


class LongRunningController:
    """Controller untuk long running mission.

    Method:
      save_checkpoint(mission_id, step_index, state, note) -> bool
      record_retry(mission_id, step_id, reason) -> bool
      record_approval(mission_id, decision_id, result) -> bool
      record_verification(mission_id, step_id, passed) -> bool
      update_elapsed(mission_id, seconds) -> bool
      get_checkpoint(mission_id) -> Optional[Checkpoint]
      restore(mission_id) -> bool  # restart dari checkpoint
    """

    def __init__(self):
        self._missions: Dict[str, LongRunningMission] = {}

    def register(self, mission: LongRunningMission):
        """Daftarkan mission."""
        self._missions[mission.mission_id] = mission

    def _get(self, mission_id: str) -> Optional[LongRunningMission]:
        return self._missions.get(mission_id)

    # --- CHECKPOINT ---

    def save_checkpoint(self, mission_id: str, step_index: int,
                        state: str, note: str = "") -> bool:
        """Simpan checkpoint."""
        m = self._get(mission_id)
        if m is None:
            return False
        m.checkpoint = Checkpoint(
            step_index=step_index,
            state=state,
            note=note,
        )
        return True

    def get_checkpoint(self, mission_id: str) -> Optional[Checkpoint]:
        """Dapatkan checkpoint terakhir."""
        m = self._get(mission_id)
        return m.checkpoint if m else None

    def restore(self, mission_id: str) -> Optional[Checkpoint]:
        """Restart dari checkpoint terakhir.

        Methods: ambil checkpoint, clear retry history.
        Mission bisa dilanjutkan dari sini.
        """
        m = self._get(mission_id)
        if m is None:
            return None
        ck = m.checkpoint
        if ck is None:
            return None
        # Hapus retry yang sudah lewat (bisa di-record ulang)
        m.retries = [r for r in m.retries if r.step_id != ck.step_index]
        return ck

    # --- RETRY ---

    def record_retry(self, mission_id: str, step_id: str,
                     reason: str) -> bool:
        """Catat retry."""
        m = self._get(mission_id)
        if m is None:
            return False
        m.retry_count += 1
        m.retries.append(RetryRecord(
            step_id=step_id,
            attempt=m.retry_count,
            reason=reason,
        ))
        return True

    def get_retry_history(self, mission_id: str,
                          step_id: Optional[str] = None) -> List[RetryRecord]:
        """Dapatkan history retry. Optional filter by step."""
        m = self._get(mission_id)
        if m is None:
            return []
        if step_id:
            return [r for r in m.retries if r.step_id == step_id]
        return list(m.retries)

    # --- HISTORY ---

    def record_approval(self, mission_id: str, decision_id: str,
                        result: str) -> bool:
        """Catat approval."""
        m = self._get(mission_id)
        if m is None:
            return False
        m.approval_history.append({
            "decision_id": decision_id,
            "result": result,
            "timestamp": datetime.now().isoformat(),
        })
        return True

    def record_verification(self, mission_id: str, step_id: str,
                            passed: bool) -> bool:
        """Catat verification."""
        m = self._get(mission_id)
        if m is None:
            return False
        m.verification_history.append({
            "step_id": step_id,
            "passed": passed,
            "timestamp": datetime.now().isoformat(),
        })
        return True

    # --- ELAPSED ---

    def update_elapsed(self, mission_id: str, seconds: float) -> bool:
        """Update elapsed time."""
        m = self._get(mission_id)
        if m is None:
            return False
        m.elapsed_seconds = seconds
        return True

    def get_status(self, mission_id: str) -> Optional[dict]:
        """Status lengkap untuk dashboard."""
        m = self._get(mission_id)
        if m is None:
            return None
        return m.to_dict()
