# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 123 - Orchestration Foundation: orchestration_builder.

Builds an orchestration plan from a request using the registry.
Arranges and directs the pipeline - never executes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional, Tuple

from .orchestration_request import OrchestrationRequest
from .orchestration_registry import OrchestrationRegistry
from .orchestration_context import OrchestrationContext


@dataclass(frozen=True)
class OrchestrationPlan:
    """Immutable plan produced by the builder."""

    request_id: str
    workflow: str
    chain: Tuple[str, ...]
    complete: bool = True

    @property
    def is_plan_only(self) -> bool:
        """A plan never executes; it only arranges."""
        return True


class OrchestrationBuilder:
    """Arranges runtimes into an ordered orchestration plan."""

    def __init__(self, registry: OrchestrationRegistry) -> None:
        self._registry = registry

    def build(self, request: OrchestrationRequest) -> Optional[OrchestrationPlan]:
        """Build an ordered plan from the request's runtime chain."""
        if not request.runtimes:
            return None
        known = self._registry.ids()
        chain = tuple(r for r in request.runtimes if r in known)
        if not chain:
            return None
        return OrchestrationPlan(
            request_id=request.request_id,
            workflow=request.workflow,
            chain=chain,
        )

    def build_from_context(
        self,
        request: OrchestrationRequest,
        context: OrchestrationContext,
    ) -> Optional[OrchestrationPlan]:
        """Build a plan preferring the context's runtime chain."""
        chain = context.runtimes or request.runtimes
        merged = OrchestrationRequest(
            request_id=request.request_id,
            workflow=request.workflow,
            runtimes=chain,
            priority=request.priority,
            source_runtime=request.source_runtime,
            parameters=request.parameters,
        )
        return self.build(merged)
