# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 139 - Mission State: dashboard_state.

Read-only dashboard bridge for mission state (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .mission_state import MissionState


class DashboardStateBridge:
    """Read-only bridge presenting mission state as cards."""

    def cards_for(self, state: MissionState) -> Tuple[ExecutionCard, ...]:
        return (
            ExecutionCard(
                card_id="st-mission",
                title="Mission",
                summary=state.mission_id,
                detail="State managed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="st-state",
                title="State",
                summary=state.state,
                detail="open / active / closed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="st-stage",
                title="Stage",
                summary="{0}".format(state.stage),
                detail="Lifecycle progress",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="st-history",
                title="Transitions Tracked",
                summary="History recorded",
                detail="Append-only, sync",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="st-sprint",
                title="State Sprint 139",
                summary="State, registry, transition, validator, history",
                detail="Mission State",
                verdict="ready",
            ),
        )

    def verdict_card(self, state: MissionState) -> ExecutionCard:
        return ExecutionCard(
            card_id="st-status",
            title="Mission State Managed",
            summary="state={0}".format(state.state),
            detail="State only - no execution",
            verdict="ready",
        )
