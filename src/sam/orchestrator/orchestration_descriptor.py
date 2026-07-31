# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 123 - Orchestration Foundation: orchestration_descriptor.

Describes a runtime that can participate in orchestration.
Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class OrchestrationDescriptor:
    """Immutable description of a runnable runtime in the orchestration.

    Identifies the runtime, its role, and its position in the global
    pipeline order. Describing is not executing.
    """

    runtime_id: str
    name: str
    category: str = "runtime"
    description: str = ""
    pipeline_position: int = 0
    capabilities: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_orchestratable(self) -> bool:
        """Every runtime with an id is orchestratable (planning only)."""
        return bool(self.runtime_id)
