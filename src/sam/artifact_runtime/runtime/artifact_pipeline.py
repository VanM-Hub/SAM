"""ArtifactPipeline — pipeline Descriptor->Artifact->Builder->Preview."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from ..foundation.artifact_descriptor import ArtifactDescriptor
from ..runtime.artifact_runtime import ArtifactRuntime, ArtifactRunResult


@dataclass(frozen=True)
class ArtifactPipelineStage:
    name: str
    ok: bool = True


@dataclass(frozen=True)
class ArtifactPipelineRun:
    ok: bool = True
    stages: Tuple[ArtifactPipelineStage, ...] = ()
    external_calls: int = 0


class ArtifactPipeline:
    """Pipeline representasi artifact (read-only, no storage)."""

    def __init__(self, runtime: ArtifactRuntime) -> None:
        self._runtime = runtime

    def route(self) -> Tuple[str, ...]:
        return ("descriptor", "artifact", "builder", "preview")

    def run(self, name: str, kind: str = "report",
            descriptor: ArtifactDescriptor = ArtifactDescriptor("default")
            ) -> ArtifactPipelineRun:
        stages = (
            ArtifactPipelineStage("descriptor", ok=True),
            ArtifactPipelineStage("artifact", ok=bool(name)),
            ArtifactPipelineStage("builder", ok=True),
            ArtifactPipelineStage("preview", ok=True),
        )
        res = self._runtime.run(name, kind)
        return ArtifactPipelineRun(ok=res.ok, stages=stages, external_calls=0)
