"""Recovery Restore — resume state dari checkpoint.

Menutup gap H2 (EA-001-002 D2-G1): setelah crash/restart, state bisa di-
resume dari checkpoint terbaru. Restore melakukan verifikasi checksum agar
state yang korup/berubah tidak dipakai (anti silent corruption).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sam.recovery.checkpoint import Checkpoint, CheckpointManager, CheckpointState
from sam.recovery.manifest import CheckpointIndex, CorruptCheckpointError, CheckpointNotFound
from sam.recovery.state import CheckpointState as _CS


@dataclass(frozen=True)
class RecoveryResult:
    """Hasil operasi restore."""

    restored: bool
    checkpoint_id: str = ""
    scope: str = ""
    state: Dict[str, Any] = field(default_factory=dict)
    checksum_verified: bool = False
    reason: str = ""

    @property
    def ok(self) -> bool:
        return self.restored


class RestoreManager:
    """Restore state dari checkpoint (dengan verifikasi checksum)."""

    def __init__(self, manager: CheckpointManager) -> None:
        self._manager = manager
        self._index = CheckpointIndex(manager)

    def verify_checksum(self, ckpt: Checkpoint) -> bool:
        """Verifikasi payload state cocok checksum (anti korupsi/tamper)."""
        return _CS.compute_checksum(ckpt.state) == ckpt.checksum_sha256

    def restore_latest(self, scope: str) -> RecoveryResult:
        """Restore checkpoint terbaru untuk scope. Gagal bila tak ada / korup."""
        ckpt = self._index.latest(scope)
        if ckpt is None:
            return RecoveryResult(False, scope=scope, reason="no checkpoint")
        return self.restore(scope, ckpt.checkpoint_id)

    def restore(self, scope: str, checkpoint_id: str) -> RecoveryResult:
        """Restore checkpoint tertentu — verifikasi checksum sebelum dipakai."""
        try:
            ckpt = self._index.load(scope, checkpoint_id)
        except CheckpointNotFound:
            return RecoveryResult(False, scope=scope, checkpoint_id=checkpoint_id,
                                  reason="not found")
        except CorruptCheckpointError as exc:
            return RecoveryResult(False, scope=scope, checkpoint_id=checkpoint_id,
                                  reason=f"corrupt: {exc}")

        if not self.verify_checksum(ckpt):
            return RecoveryResult(
                False, checkpoint_id=checkpoint_id, scope=scope,
                reason="checksum mismatch (corrupt or tampered)",
            )
        return RecoveryResult(
            True, checkpoint_id=ckpt.checkpoint_id, scope=ckpt.scope,
            state=dict(ckpt.state), checksum_verified=True, reason="ok",
        )
