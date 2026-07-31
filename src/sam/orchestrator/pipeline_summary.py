# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 126 - Pipeline Builder: pipeline_summary.

Summarizes a built pipeline. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PipelineSummary:
    """Immutable summary of a pipeline."""

    pipeline_id: str
    runtime_ids: Tuple[str, ...]
    total_stages: int = 0
