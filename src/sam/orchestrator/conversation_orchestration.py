# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 123 - Orchestration Foundation: conversation_orchestration.

Read-only conversation bridge. Returns cheap, deterministic summaries.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from .orchestration_registry import OrchestrationRegistry
from .orchestration_builder import OrchestrationBuilder, OrchestrationPlan
from .orchestration_request import OrchestrationRequest


class ConversationOrchestrationBridge:
    """Read-only bridge exposing orchestration info for conversation."""

    def __init__(self, registry: OrchestrationRegistry) -> None:
        self._registry = registry
        self._builder = OrchestrationBuilder(registry)

    def count_runtimes(self) -> int:
        return self._registry.count()

    def list_runtimes(self) -> Tuple[str, ...]:
        return tuple(d.name for d in self._registry.all())

    def describe(self, runtime_id: str) -> str:
        d = self._registry.get(runtime_id)
        return d.description if d else ""

    def plan(self, request: OrchestrationRequest) -> Optional[OrchestrationPlan]:
        return self._builder.build(request)

    def summary(self) -> Dict[str, int]:
        return {"runtimes": self._registry.count()}
