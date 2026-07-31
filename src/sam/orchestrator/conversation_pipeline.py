# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 126 - Pipeline Builder: conversation_pipeline.

Read-only conversation bridge for pipeline building.
"""
from __future__ import annotations

from typing import Dict, Tuple

from .pipeline_builder import PipelineBuilder, BuiltPipeline


class ConversationPipelineBridge:
    """Read-only bridge exposing pipeline building."""

    def __init__(self, builder: PipelineBuilder) -> None:
        self._builder = builder

    def build(self, pipeline_id: str, chain: Tuple[str, ...]) -> BuiltPipeline:
        return self._builder.build(pipeline_id, chain)

    def runtime_ids(self, pipeline: BuiltPipeline) -> Tuple[str, ...]:
        return pipeline.runtime_ids

    def stage_count(self, pipeline: BuiltPipeline) -> int:
        return pipeline.stage_count

    def summary(self, pipeline: BuiltPipeline) -> Dict[str, int]:
        return {"stages": pipeline.stage_count}
