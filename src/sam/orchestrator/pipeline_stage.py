# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 126 - Pipeline Builder: pipeline_stage.

A single stage in an orchestration pipeline. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineStage:
    """Immutable description of one pipeline stage."""

    stage_id: str
    runtime_id: str
    order: int = 0
    name: str = ""
