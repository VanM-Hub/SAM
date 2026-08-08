"""Recovery Checkpoint — simpan state ke disk (atomic, ber-checksum).

Menutup gap H2 (EA-001-002 D2-G1): menyediakan kemampuan capture state ->
simpan persist -> metadata. Atomic write (temp + rename) mencegah file
setengah-tulis bila proses crash di tengah penyimpanan.
"""

from __future__ import annotations

import json
import os
import tempfile
import time
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from sam.recovery.state import CheckpointState, SnapshotMetadata


def _now_ms() -> float:
    return time.time()


@dataclass(frozen=True)
class RetentionPolicy:
    """Kebijakan retensi checkpoint per scope."""

    max_checkpoints: int = 10            # jumlah maksimum checkpoint disimpan
    scope: str = "default"


@dataclass(frozen=True)
class Checkpoint:
    """Checkpoint persisten + metadata yang sudah dihitung."""

    checkpoint_id: str
    scope: str
    created_at: str
    checksum_sha256: str
    state: Dict[str, Any]
    data_version: int = 1

    def to_dict(self) -> dict:
        return {
            "checkpoint_id": self.checkpoint_id,
            "scope": self.scope,
            "created_at": self.created_at,
            "checksum_sha256": self.checksum_sha256,
            "data_version": self.data_version,
            "state": self.state,
        }

    @staticmethod
    def from_dict(data: dict) -> "Checkpoint":
        return Checkpoint(
            checkpoint_id=data["checkpoint_id"],
            scope=data["scope"],
            created_at=data["created_at"],
            checksum_sha256=data["checksum_sha256"],
            data_version=data.get("data_version", 1),
            state=data.get("state", {}),
        )


class CheckpointManager:
    """Manajer checkpoint: capture, persist (atomic), skema file.

    Layout file: `<state_dir>/<scope>/<checkpoint_id>.json`.
    Atomic write: tulis ke file temp di direktori sama -> fsync -> rename.
    """

    def __init__(self, state_dir: str, encoding: str = "utf-8") -> None:
        self._dir = state_dir
        self._encoding = encoding

    # ---- location ----

    def _scope_dir(self, scope: str) -> str:
        safe = scope.replace("/", "_").replace("\\", "_").replace(":", "_")
        return os.path.join(self._dir, safe)

    def checkpoint_path(self, scope: str, checkpoint_id: str) -> str:
        return os.path.join(self._scope_dir(scope), f"{checkpoint_id}.json")

    # ---- capture & persist ----

    def capture(
        self,
        scope: str,
        state: Dict[str, Any],
        *,
        checkpoint_id: Optional[str] = None,
        data_version: int = 1,
    ) -> CheckpointState:
        """Capture state menjadi CheckpointState (belum ditulis ke disk)."""
        from sam.recovery.state import CheckpointState, SnapshotMetadata

        cid = checkpoint_id or f"ckpt-{uuid.uuid4().hex[:12]}"
        checksum = CheckpointState.compute_checksum(state)
        meta = SnapshotMetadata(
            checkpoint_id=cid,
            scope=scope,
            created_at=_utcnow_iso(),
            checksum_sha256=checksum,
            data_version=data_version,
        )
        return CheckpointState(scope=scope, state=state, metadata=meta)

    def persist(self, cp: CheckpointState) -> Checkpoint:
        """Tulis checkpoint ke disk secara atomic + kembalikan Checkpoint."""
        scope_dir = self._scope_dir(cp.scope)
        os.makedirs(scope_dir, exist_ok=True)
        ckpt = Checkpoint(
            checkpoint_id=cp.metadata.checkpoint_id,
            scope=cp.scope,
            created_at=cp.metadata.created_at,
            checksum_sha256=cp.metadata.checksum_sha256,
            state=cp.state,
            data_version=cp.metadata.data_version,
        )
        final_path = self.checkpoint_path(cp.scope, ckpt.checkpoint_id)
        payload = json.dumps(ckpt.to_dict(), ensure_ascii=True, sort_keys=True)
        self._atomic_write(final_path, payload)
        return ckpt

    def _atomic_write(self, final_path: str, payload: str) -> None:
        directory = os.path.dirname(final_path)
        fd, tmp_path = tempfile.mkstemp(dir=directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding=self._encoding) as f:
                f.write(payload)
                f.flush()
                os.fsync(f.fileno())
            os.replace(tmp_path, final_path)  # atomic rename (Windows support)
        except BaseException:
            try:
                os.remove(tmp_path)
            except OSError:
                pass
            raise

    # ---- lifecycle ----

    def list_checkpoints(self, scope: str) -> list[str]:
        """Daftar checkpoint_id yang tersimpan (diurutkan ascending)."""
        scope_dir = self._scope_dir(scope)
        if not os.path.isdir(scope_dir):
            return []
        names = [n for n in os.listdir(scope_dir) if n.endswith(".json")]
        return sorted(n[:-5] for n in names)

    def apply_retention(self, scope: str, policy: RetentionPolicy) -> list[str]:
        """Terapkan retensi: hapus checkpoint terlama melebihi max_checkpoints."""
        ids = self.list_checkpoints(scope)
        if len(ids) <= policy.max_checkpoints:
            return []
        to_remove = ids[: len(ids) - policy.max_checkpoints]
        for cid in to_remove:
            try:
                os.remove(self.checkpoint_path(scope, cid))
            except OSError:
                pass
        return to_remove


def _utcnow_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).isoformat()
