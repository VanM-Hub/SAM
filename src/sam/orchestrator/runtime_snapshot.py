# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 132 - Runtime Engine: runtime_snapshot.

Snapshot of the runtime engine state. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass

from .runtime_status import RuntimeStatus
from .runtime_pipeline import RuntimePipeline


@dataclass(frozen=True)
class RuntimeSnapshot:
    """Immutable snapshot of the orchestration engine."""

    status: RuntimeStatus
    pipeline: RuntimePipeline
    engine_version: str = "1.0.0"

    @property
    def ready(self) -> bool:
        return self.status.is_ready
