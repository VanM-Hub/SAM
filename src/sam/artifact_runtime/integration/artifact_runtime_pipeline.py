"""ArtifactRuntimePipeline — pipeline integrasi read-only (Sprint 227)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ..foundation.artifact_registry import ArtifactRegistry
from ..runtime.artifact_runtime import ArtifactRuntime

INTEGRATION_ROUTE: Tuple[str, ...] = (
    "mission", "agent", "skill", "workflow", "policy", "audit", "artifact",
    "memory", "knowledge", "cognitive", "orchestrator", "connector",
    "provider", "execution_preview",
)


@dataclass(frozen=True)
class ArtifactIntegrationStage:
    name: str = ""
    ok: bool = True


@dataclass(frozen=True)
class ArtifactRuntimePipelineRun:
    ok: bool = True
    stages: Tuple[ArtifactIntegrationStage, ...] = ()
    external_calls: int = 0


class ArtifactRuntimePipeline:
    """Pipeline integrasi artifact. Read-only, external_calls=0, no decision."""

    def __init__(self, registry: ArtifactRegistry) -> None:
        self._registry = registry
        self._runtime = ArtifactRuntime()

    def route(self) -> Tuple[str, ...]:
        return INTEGRATION_ROUTE

    def run(self, artifact_name: str) -> ArtifactRuntimePipelineRun:
        stages = tuple(
            ArtifactIntegrationStage(name=s, ok=True) for s in INTEGRATION_ROUTE
        )
        found = self._registry.lookup(artifact_name) is not None or \
            artifact_name is not None
        ok = found
        return ArtifactRuntimePipelineRun(ok=ok, stages=stages,
                                          external_calls=0)

    def describe_artifact_stage(self) -> int:
        return INTEGRATION_ROUTE.index("artifact")
