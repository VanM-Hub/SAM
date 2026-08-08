"""Recovery Manifest — index & enumerasi checkpoint yang tersimpan.

Menyediakan query: latest, list, by time, lookup id — untuk konsumen recovery
menemukan checkpoint yang akan di-restore. Tidak mengubah runtime existing.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional

from sam.recovery.checkpoint import Checkpoint, CheckpointManager


class CheckpointNotFound(Exception):
    """Checkpoint yang diminta tidak tersedia."""


class CorruptCheckpointError(Exception):
    """Checkpoint ada tapi tidak bisa dibaca / checksum tidak cocok."""


class CheckpointIndex:
    """Index checkpoint yang tersimpan di state_dir."""

    def __init__(self, manager: CheckpointManager) -> None:
        self._manager = manager

    def list_scopes(self) -> List[str]:
        if not os.path.isdir(self._manager._dir):
            return []
        return sorted(
            n for n in os.listdir(self._manager._dir)
            if os.path.isdir(os.path.join(self._manager._dir, n))
        )

    def list_checkpoints(self, scope: str) -> List[Checkpoint]:
        """Enumerasi semua checkpoint scope (diurutkan ascending by id/time)."""
        out: List[Checkpoint] = []
        for cid in self._manager.list_checkpoints(scope):
            try:
                out.append(self.load(scope, cid))
            except (CorruptCheckpointError, CheckpointNotFound):
                continue
        return out

    def latest(self, scope: str) -> Optional[Checkpoint]:
        """Checkpoint terbaru (dengan checkpoint_id tertinggi / waktu terakhir)."""
        cps = self.list_checkpoints(scope)
        if not cps:
            return None
        return max(cps, key=lambda c: (c.created_at, c.checkpoint_id))

    def get(self, scope: str, checkpoint_id: str) -> Checkpoint:
        return self.load(scope, checkpoint_id)

    def load(self, scope: str, checkpoint_id: str) -> Checkpoint:
        path = self._manager.checkpoint_path(scope, checkpoint_id)
        if not os.path.isfile(path):
            raise CheckpointNotFound(checkpoint_id)
        try:
            with open(path, "r", encoding=self._manager._encoding) as f:
                data = json.load(f)
            ckpt = Checkpoint.from_dict(data)
        except (json.JSONDecodeError, KeyError, TypeError) as exc:
            raise CorruptCheckpointError(f"{checkpoint_id}: {exc}") from exc
        return ckpt
