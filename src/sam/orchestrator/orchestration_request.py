# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 123 - Orchestration Foundation: orchestration_request.

An incoming request for orchestration. Pure DTO, immutable.
Describes what should be orchestrated without performing it.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Optional, Tuple


@dataclass(frozen=True)
class OrchestrationRequest:
    """Immutable request to orchestrate a workflow across runtimes.

    The orchestrator orchestrates (arranges and directs), it never
    executes or approves. This DTO only carries intent.
    """

    request_id: str
    workflow: str
    runtimes: Tuple[str, ...] = ()
    priority: int = 0
    source_runtime: str = "unknown"
    parameters: Dict[str, object] = field(default_factory=dict)

    @property
    def runtime_chain(self) -> Tuple[str, ...]:
        """Ordered runtimes involved in this request."""
        return self.runtimes

    @property
    def is_preview(self) -> bool:
        """Orchestration is always preview/planning only. Always True."""
        return True
