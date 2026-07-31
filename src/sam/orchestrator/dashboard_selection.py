# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 125 - Runtime Selection: dashboard_selection.

Read-only dashboard bridge for runtime selection (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .runtime_selector import RuntimeSelection


class DashboardSelectionBridge:
    """Read-only bridge presenting selection as cards."""

    def cards_for(self, selection: RuntimeSelection) -> Tuple[ExecutionCard, ...]:
        chain = ", ".join(selection.chain) or "-"
        return (
            ExecutionCard(
                card_id="sel-chain",
                title="Selected Runtime Chain",
                summary="{0} runtime(s)".format(len(selection.chain)),
                detail=chain,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sel-scores",
                title="Selection Scores",
                summary="Per-runtime scores",
                detail="Ranked by policy",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sel-policy",
                title="Selection Policy Applied",
                summary="Policy-based ranking",
                detail="No execution performed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sel-summary",
                title="Selection Summary",
                summary="Ordered chain produced",
                detail="Arranges, does not run",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="sel-sprint",
                title="Selection Sprint 125",
                summary="Selector, policy, score, summary, validator",
                detail="Runtime Selection",
                verdict="ready",
            ),
        )

    def verdict_card(self, selection: RuntimeSelection) -> ExecutionCard:
        return ExecutionCard(
            card_id="sel-status",
            title="Selection Ready",
            summary="chain of {0} runtime(s)".format(len(selection.chain)),
            detail="Selection only - no execution",
            verdict="ready",
        )
