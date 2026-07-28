"""
OP-125 — Workspace Lock.

Mission dapat mengunci workspace.
Lock sederhana: timeout, release otomatis, cegah concurrent akses ke resource yang sama.

Resource = string key (misal: "disk_cleanup", "network_check", "db_migration").
Hanya satu mission boleh pegang lock untuk resource yang sama dalam satu waktu.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import time


@dataclass
class WorkspaceLock:
    """Satu lock.

    Attributes:
      resource: Nama resource yang dikunci (misal: "disk_cleanup")
      mission_id: ID mission yang memegang lock
      acquired_at: Timestamp lock diambil
      timeout_seconds: Lock otomatis release setelah timeout
      reason: Alasan lock (optional)
    """
    resource: str
    mission_id: str
    acquired_at: float = field(default_factory=time.time)
    timeout_seconds: int = 300   # default 5 menit
    reason: str = ""

    @property
    def is_expired(self) -> bool:
        return (time.time() - self.acquired_at) > self.timeout_seconds

    @property
    def elapsed_seconds(self) -> float:
        return time.time() - self.acquired_at

    def to_dict(self) -> dict:
        return {
            "resource": self.resource,
            "mission_id": self.mission_id,
            "acquired_at": datetime.fromtimestamp(self.acquired_at).isoformat(),
            "timeout_seconds": self.timeout_seconds,
            "is_expired": self.is_expired,
            "elapsed_seconds": round(self.elapsed_seconds, 1),
            "reason": self.reason,
        }

    def to_summary(self) -> str:
        status = "EXPIRED" if self.is_expired else "ACTIVE"
        return "[{}] {} held by {} ({:.0f}s elapsed, timeout {}s)".format(
            status, self.resource, self.mission_id,
            self.elapsed_seconds, self.timeout_seconds)


class WorkspaceLockManager:
    """Manager untuk workspace locks.

    Method:
      acquire(resource, mission_id, timeout_seconds, reason) -> bool
      release(resource, mission_id) -> bool
      is_locked(resource) -> bool
      get_lock(resource) -> Optional[WorkspaceLock]
      get_locks_by_mission(mission_id) -> List[WorkspaceLock]
      release_expired() -> int  # bersihkan lock expired
      release_all(mission_id) -> int  # lepas semua lock mission
      reset()
    """

    def __init__(self):
        self._locks: Dict[str, WorkspaceLock] = {}

    def acquire(self, resource: str, mission_id: str,
                timeout_seconds: int = 300, reason: str = "") -> bool:
        """Coba acquire lock untuk resource.

        Returns:
          True jika lock berhasil diambil
          False jika sudah dipegang mission lain (atau expired)
        """
        # Bersihkan expired dulu
        self._release_expired_for(resource)

        existing = self._locks.get(resource)
        if existing is not None:
            if existing.mission_id == mission_id:
                return True  # Sudah pegang — no-op
            return False  # Dipegang mission lain

        self._locks[resource] = WorkspaceLock(
            resource=resource,
            mission_id=mission_id,
            timeout_seconds=timeout_seconds,
            reason=reason,
        )
        return True

    def release(self, resource: str, mission_id: str) -> bool:
        """Release lock. Hanya oleh pemiliknya."""
        existing = self._locks.get(resource)
        if existing is None:
            return True  # sudah tidak ada lock
        if existing.mission_id != mission_id:
            return False  # bukan pemilik
        del self._locks[resource]
        return True

    def is_locked(self, resource: str) -> bool:
        """Cek apakah resource terkunci (dan belum expired)."""
        existing = self._locks.get(resource)
        if existing is None:
            return False
        if existing.is_expired:
            del self._locks[resource]
            return False
        return True

    def get_lock(self, resource: str) -> Optional[WorkspaceLock]:
        """Dapatkan lock detail. Otomatis bersihkan expired."""
        existing = self._locks.get(resource)
        if existing is None:
            return None
        if existing.is_expired:
            del self._locks[resource]
            return None
        return existing

    def get_locks_by_mission(self, mission_id: str) -> List[WorkspaceLock]:
        """Semua lock yang dipegang mission."""
        self.release_expired()
        return [l for l in self._locks.values() if l.mission_id == mission_id]

    def release_expired(self) -> int:
        """Release semua lock expired. Return count."""
        expired = [r for r, l in self._locks.items() if l.is_expired]
        for r in expired:
            del self._locks[r]
        return len(expired)

    def _release_expired_for(self, resource: str):
        """Release expired lock untuk resource tertentu."""
        existing = self._locks.get(resource)
        if existing and existing.is_expired:
            del self._locks[resource]

    def release_all(self, mission_id: str) -> int:
        """Release semua lock milik mission. Return count."""
        to_release = [
            r for r, l in self._locks.items()
            if l.mission_id == mission_id
        ]
        for r in to_release:
            del self._locks[r]
        return len(to_release)

    def list_locks(self) -> List[WorkspaceLock]:
        """Semua lock aktif (tidak expired)."""
        self.release_expired()
        return list(self._locks.values())

    @property
    def active_count(self) -> int:
        return len(self.list_locks())

    def reset(self):
        self._locks.clear()
