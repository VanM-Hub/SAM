# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 130 - Synchronization: dashboard_sync.

Read-only dashboard bridge for synchronization (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .sync_snapshot import SyncSnapshot


class DashboardSyncBridge:
    """Read-only bridge presenting sync state as cards."""

    def cards_for(self, snapshot: SyncSnapshot) -> Tuple[ExecutionCard, ...]:
        runtimes = ", ".join(s.runtime_id for s in snapshot.states) or "-"
        return (
            ExecutionCard(
                card_id="sync-runtimes",
                title="Synchronized Runtimes",
                summary="{0}/{1} synced".format(snapshot.synchronized_count, snapshot.total),
                detail=runtimes,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sync-all",
                title="All Synchronized",
                summary=str(snapshot.all_synchronized),
                detail="Deterministic sync state",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sync-validated",
                title="Sync Validated",
                summary="States well-formed",
                detail="No duplicates/empty",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sync-snapshot",
                title="Snapshot Captured",
                summary="Sync state frozen",
                detail="Plan only - not run",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sync-sprint",
                title="Synchronization Sprint 130",
                summary="Request, snapshot, state, validator, summary",
                detail="Synchronization",
                verdict="ready",
            ),
        )

    def verdict_card(self, snapshot: SyncSnapshot) -> ExecutionCard:
        return ExecutionCard(
            card_id="sync-status",
            title="Synchronized",
            summary="{0} runtime(s) in sync".format(snapshot.synchronized_count),
            detail="Synchronization only - no execution",
            verdict="ready",
        )
