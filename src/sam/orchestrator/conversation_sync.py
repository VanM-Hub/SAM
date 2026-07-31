# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 130 - Synchronization: conversation_sync.

Read-only conversation bridge for synchronization.
"""
from __future__ import annotations

from typing import Dict, Tuple

from .sync_request import SyncRequest
from .sync_snapshot import SyncSnapshot
from .sync_state import SyncState


class ConversationSyncBridge:
    """Read-only bridge exposing synchronization info."""

    def sync(self, request: SyncRequest) -> SyncSnapshot:
        """Build a snapshot marking all runtimes synchronized (plan only)."""
        states = tuple(
            SyncState(runtime_id=runtime_id, state="synchronized")
            for runtime_id in request.runtimes
        )
        return SyncSnapshot(sync_id=request.sync_id, states=states)

    def synchronized(self, snapshot: SyncSnapshot) -> int:
        return snapshot.synchronized_count

    def summary(self, snapshot: SyncSnapshot) -> Dict[str, int]:
        return {
            "synchronized": snapshot.synchronized_count,
            "total": snapshot.total,
        }
