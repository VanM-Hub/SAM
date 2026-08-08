"""SAM Recovery — Runtime Checkpoint & Recovery.

Menutup gap H2 (Priority P3, Program D / MISSION-2D, EA-001-002 D2-G1):
"Tidak ada checkpoint/snapshot recovery state runtime" — runtime state tidak
dapat di-resume setelah crash; restart = mulai bersih + re-migrate.

Desain (konservatif terhadap constraint EA-002):
- Modul recovery berdiri sendiri (stand-alone) sebagai capability baru.
- TIDAK mengubah responsibility runtime existing (runtime_kernel, approval,
  guardian) — menyediakan mekanisme GENERIC checkpoint/save/restore yang bisa
  dipakai oleh consumer runtime TANPA mengubah lapisan tersebut.
- Persistensi ke disk memakai atomic write (temp file + rename) + checksum
  (SHA-256) untuk deteksi korupsi.
- State directory default: `data/checkpoints/` (di-ignore git).
"""

from __future__ import annotations

from sam.recovery.checkpoint import (
    Checkpoint,
    CheckpointManager,
    RetentionPolicy,
)
from sam.recovery.manifest import (
    CheckpointIndex,
    CheckpointNotFound,
    CorruptCheckpointError,
)
from sam.recovery.restore import RecoveryResult, RestoreManager
from sam.recovery.audit import CheckpointAuditRecord, CheckpointAuditLog
from sam.recovery.state import CheckpointState, SnapshotMetadata

__all__ = [
    "Checkpoint",
    "CheckpointAuditLog",
    "CheckpointAuditRecord",
    "CheckpointIndex",
    "CheckpointManager",
    "CheckpointNotFound",
    "CheckpointState",
    "CorruptCheckpointError",
    "RecoveryResult",
    "RestoreManager",
    "RetentionPolicy",
    "SnapshotMetadata",
]
