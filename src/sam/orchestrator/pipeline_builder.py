# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 126 - Pipeline Builder: pipeline_builder.

Builds a pipeline (ordered stages) from a selected runtime chain.
Arranges stages - never executes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple

from .pipeline_stage import PipelineStage


@dataclass(frozen=True)
class BuiltPipeline:
    """Immutable pipeline made of ordered stages."""

    pipeline_id: str
    stages: Tuple[PipelineStage, ...] = field(default_factory=tuple)

    @property
    def stage_count(self) -> int:
        return len(self.stages)

    @property
    def runtime_ids(self) -> Tuple[str, ...]:
        return tuple(s.runtime_id for s in self.stages)


class PipelineBuilder:
    """Builds stages from a runtime chain in order."""

    def __init__(self) -> None:
        self._names: Dict[str, str] = {}

    def register_names(self, names: Dict[str, str]) -> None:
        """Register runtime_id to display name mapping."""
        self._names.update(names)

    def build(self, pipeline_id: str, chain: Tuple[str, ...]) -> BuiltPipeline:
        """Create a pipeline with one stage per runtime in-chain."""
        stages = tuple(
            PipelineStage(
                stage_id="{0}-{1}".format(pipeline_id, idx),
                runtime_id=runtime_id,
                order=idx,
                name=self._names.get(runtime_id, runtime_id),
            )
            for idx, runtime_id in enumerate(chain)
        )
        return BuiltPipeline(pipeline_id=pipeline_id, stages=stages)
