# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 130 - Synchronization: sync_snapshot.

Snapshot of synchronization across runtimes. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .sync_state import SyncState


@dataclass(frozen=True)
class SyncSnapshot:
    """Immutable snapshot of sync states."""

    sync_id: str
    states: Tuple[SyncState, ...] = field(default_factory=tuple)

    @property
    def synchronized_count(self) -> int:
        return sum(1 for s in self.states if s.is_synchronized)

    @property
    def total(self) -> int:
        return len(self.states)

    @property
    def all_synchronized(self) -> bool:
        return bool(self.states) and self.synchronized_count == self.total
