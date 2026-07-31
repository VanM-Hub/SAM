"""Cognitive Pipeline — pipeline kognitif (Sprint 191)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..context.cognitive_context import CognitiveContext
from ..context.cognitive_snapshot import CognitiveSnapshot
from ..foundation.cognitive_registry import CognitiveRegistry


@dataclass(frozen=True)
class CognitivePipelineStage:
    """Satu tahap pipeline (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class CognitivePipelineRun:
    """Hasil pipeline (immutable)."""
    ok: bool = False
    stages: List[CognitivePipelineStage] = field(default_factory=list)
    external_calls: int = 0


class CognitivePipeline:
    """Pipeline: Descriptor → Context → Snapshot → Workspace → Preview."""

    STAGES = ["descriptor", "context", "snapshot", "workspace", "preview"]

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def stages(self) -> List[str]:
        return list(self.STAGES)

    def run(self, cognitive_id: str) -> CognitivePipelineRun:
        stages = []
        ok = self._registry.exists(cognitive_id)
        stages.append(CognitivePipelineStage(
            "descriptor", ok, "found" if ok else "not found",
        ))
        if not ok:
            return CognitivePipelineRun(ok=False, stages=stages, external_calls=0)
        for name in ["context", "snapshot", "workspace", "preview"]:
            stages.append(CognitivePipelineStage(name, True, "read-only"))
        return CognitivePipelineRun(ok=True, stages=stages, external_calls=0)
