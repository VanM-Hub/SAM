# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 135 - Mission Definition: dashboard_definition.

Read-only dashboard bridge for mission definition (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .mission_definition import MissionDefinition


class DashboardDefinitionBridge:
    """Read-only bridge presenting mission definition as cards."""

    def cards_for(self, definition: MissionDefinition) -> Tuple[ExecutionCard, ...]:
        modules = ", ".join(definition.scope.modules) or "-"
        return (
            ExecutionCard(
                card_id="def-id",
                title="Mission ID",
                summary=definition.mission_id,
                detail="Definition focused",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="def-scope",
                title="Scope",
                summary="Domain {0}".format(definition.scope.domain),
                detail=modules,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="def-constraints",
                title="Constraints",
                summary="plan-only={0}".format(definition.constraints.is_plan_only),
                detail="max objections={0}".format(definition.constraints.max_objectives),
                verdict="ready",
            ),
            ExecutionCard(
                card_id="def-validated",
                title="Definition Validated",
                summary="Well-formed definition",
                detail="No execution performed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="def-sprint",
                title="Definition Sprint 135",
                summary="Definition, scope, constraints, metadata, validator",
                detail="Mission Definition",
                verdict="ready",
            ),
        )

    def verdict_card(self, definition: MissionDefinition) -> ExecutionCard:
        return ExecutionCard(
            card_id="def-status",
            title="Mission Defined",
            summary="{0} defined".format(definition.mission_id),
            detail="Definition only - no execution",
            verdict="ready",
        )
