"""Provider Runtime Pipeline — pipeline preview terpadu.

Sprint 154 — Provider Runtime.
Mengorkestrasi discovery -> routing -> preview. Semua preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from ..registry.provider_registry import ProviderRegistry
from ..discovery.provider_discovery import ProviderDiscovery
from ..routing.provider_router import ProviderRouter, RoutingDecision


@dataclass(frozen=True)
class PipelineStep:
    """Satu langkah pipeline (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class PipelineResult:
    """Hasil pipeline (immutable)."""
    ok: bool = False
    provider_id: Optional[str] = None
    steps: List[PipelineStep] = field(default_factory=list)


class ProviderRuntimePipeline:
    """Pipeline provider runtime. Deterministik, preview-only."""

    def __init__(self, registry: ProviderRegistry) -> None:
        self._registry = registry
        self._discovery = ProviderDiscovery(registry)
        self._router = ProviderRouter(registry)

    def run(self, operation: str) -> PipelineResult:
        steps = []
        # discovery
        candidates = self._discovery.all()
        steps.append(PipelineStep("discovery", bool(candidates), f"{len(candidates)} provider(s)"))
        if not candidates:
            return PipelineResult(ok=False, steps=steps)
        # routing
        decision = self._router.route(operation)
        steps.append(PipelineStep(
            "routing", decision.matched,
            decision.provider_id or "no-match",
        ))
        if not decision.matched:
            return PipelineResult(ok=False, steps=steps)
        # preview plan (always external_calls 0)
        steps.append(PipelineStep("preview", True, "external_calls=0"))
        return PipelineResult(ok=True, provider_id=decision.provider_id, steps=steps)
