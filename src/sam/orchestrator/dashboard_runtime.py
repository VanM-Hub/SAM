# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 124 - Runtime Discovery: dashboard_runtime.

Read-only dashboard bridge for runtime discovery (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .runtime_catalog import RuntimeCatalog


class DashboardRuntimeBridge:
    """Read-only bridge presenting discovery as cards."""

    def __init__(self, catalog: RuntimeCatalog) -> None:
        self._catalog = catalog

    def cards(self) -> Tuple[ExecutionCard, ...]:
        total = self._catalog.count()
        names = ", ".join(d.name for d in self._catalog.all()) or "-"
        return (
            ExecutionCard(
                card_id="disc-total",
                title="Discovered Runtimes",
                summary="{0} runtime(s)".format(total),
                detail=names,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="disc-inventory",
                title="Inventory Built",
                summary="Available runtime inventory",
                detail="From catalog, ordered by pipeline",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="disc-locator",
                title="Locator Ready",
                summary="Find by id/position/tag",
                detail="Sync, deterministic",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="disc-validator",
                title="Discovery Validated",
                summary="Well-formed descriptors",
                detail="No action performed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="disc-sprint",
                title="Discovery Sprint 124",
                summary="Descriptor, catalog, locator, inventory, validator",
                detail="Runtime Discovery",
                verdict="ready",
            ),
        )

    def verdict_card(self) -> ExecutionCard:
        return ExecutionCard(
            card_id="disc-status",
            title="Discovery Ready",
            summary="runtimes inventory available",
            detail="Discovery only - no execution",
            verdict="ready",
        )
