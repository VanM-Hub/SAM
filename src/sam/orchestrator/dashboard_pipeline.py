# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 126 - Pipeline Builder: dashboard_pipeline.

Read-only dashboard bridge for pipeline building (5 ExecutionCards).
"""
from __future__ import annotations

from typing import Tuple

from sam.connectors.dashboard_connector import ExecutionCard
from .pipeline_builder import BuiltPipeline


class DashboardPipelineBridge:
    """Read-only bridge presenting pipeline as cards."""

    def cards_for(self, pipeline: BuiltPipeline) -> Tuple[ExecutionCard, ...]:
        runtimes = ", ".join(pipeline.runtime_ids) or "-"
        return (
            ExecutionCard(
                card_id="pipe-stages",
                title="Pipeline Stages",
                summary="{0} stage(s)".format(pipeline.stage_count),
                detail=runtimes,
                verdict="ready",
            ),
            ExecutionCard(
                card_id="pipe-order",
                title="Pipeline Ordered",
                summary="Stages in execution order",
                detail="Arranged from runtime chain",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="pipe-builder",
                title="Pipeline Builder",
                summary="Stages built from chain",
                detail="No execution performed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="pipe-validated",
                title="Pipeline Validated",
                summary="Well-formed pipeline",
                detail="Order/stage checks passed",
                verdict="ready",
            ),
            ExecutionCard(
                card_id="pipe-sprint",
                title="Pipeline Sprint 126",
                summary="Descriptor, builder, stage, validator, summary",
                detail="Pipeline Builder",
                verdict="ready",
            ),
        )

    def verdict_card(self, pipeline: BuiltPipeline) -> ExecutionCard:
        return ExecutionCard(
            card_id="pipe-status",
            title="Pipeline Built",
            summary="{0} stage(s) ready".format(pipeline.stage_count),
            detail="Pipeline only - no execution",
            verdict="ready",
        )
