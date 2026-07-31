# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 130 - Synchronization: sync_state.

Per-runtime synchronization state. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SyncState:
    """Immutable sync state for one runtime."""

    runtime_id: str
    state: str = "pending"  # pending | synchronized

    @property
    def is_synchronized(self) -> bool:
        return self.state == "synchronized"
