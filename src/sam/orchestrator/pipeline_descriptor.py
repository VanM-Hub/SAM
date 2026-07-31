# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 126 - Pipeline Builder: pipeline_descriptor.

Describes a pipeline to be built. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class PipelineDescriptor:
    """Immutable name/version for a pipeline."""

    pipeline_id: str
    name: str = ""
    version: str = "1.0.0"
    stages: Tuple[str, ...] = field(default_factory=tuple)
