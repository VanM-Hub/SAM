# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 123 - Orchestration Foundation: orchestration_context.

Represents the execution context in which orchestration takes place.
Pure DTO, immutable, deterministic - never performs actions.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class OrchestrationContext:
    """Immutable snapshot of the environment for an orchestration run.

    Carries the originating runtime chain (in order) plus lightweight
    metadata. It describes *where* an orchestration happens without
    executing anything.
    """

    request_id: str
    source_runtime: str
    target_runtime: Optional[str] = None
    runtimes: Tuple[str, ...] = ()
    tags: Tuple[str, ...] = ()
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def runtime_chain(self) -> Tuple[str, ...]:
        """Read-only runtime chain this context represents."""
        return self.runtimes
