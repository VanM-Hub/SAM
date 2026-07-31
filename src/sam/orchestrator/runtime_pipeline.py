# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 132 - Runtime Engine: runtime_pipeline.

A pipeline owned by the orchestration runtime engine. Pure DTO.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class RuntimePipeline:
    """Immutable pipeline description handled by the engine."""

    pipeline_id: str
    order: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def stage_count(self) -> int:
        return len(self.order)
