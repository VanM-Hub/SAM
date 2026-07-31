# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 137 - Mission Resources: dashboard_resource.

Read-only dashboard bridge for resources (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .resource_summary import ResourceSummary


class DashboardResourceBridge:
    """Read-only bridge presenting resources as cards."""

    def cards_for(self, summary: ResourceSummary) -> Tuple[ExecutionCard, ...]:
        ids = ", ".join(summary.allocated_ids) or "-"
        return (
            ExecutionCard(
                card_id="res-alloc",
                title="Allocated Resources",
                summary="{0} allocated".format(len(summary.allocated_ids)),
                detail=ids,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="res-total",
                title="Total Resources",
                summary="{0} available".format(summary.total),
                detail="Inventory size",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="res-allocator",
                title="Allocator Ready",
                summary="Available resources selected",
                detail="Deterministic",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="res-validated",
                title="Allocation Validated",
                summary="No duplicates",
                detail="Well-formed allocation",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="res-sprint",
                title="Resources Sprint 137",
                summary="Descriptor, inventory, allocator, validator, summary",
                detail="Mission Resources",
                verdict="ready",
            ),
        )

    def verdict_card(self, summary: ResourceSummary) -> ExecutionCard:
        return ExecutionCard(
            card_id="res-status",
            title="Resources Ready",
            summary="{0} allocated".format(len(summary.allocated_ids)),
            detail="Allocation only - no execution",
            verdict="ready",
        )
