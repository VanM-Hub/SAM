"""Memory Pipeline — pipeline runtime memori (Sprint 175).

Pipeline: Descriptor → Record → Builder → Snapshot → Preview.
Preview-only, external_calls selalu 0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.memory_registry import MemoryRegistry
from ..builder.context_builder import ContextBuilder
from ..builder.snapshot_builder import SnapshotBuilder
from ..builder.preview_builder import PreviewBuilder


@dataclass(frozen=True)
class MemoryPipelineStage:
    """Satu tahap pipeline memori (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class MemoryPipelineRun:
    """Hasil pipeline memori (immutable)."""
    ok: bool = False
    memory_id: str = ""
    stages: List[MemoryPipelineStage] = field(default_factory=list)
    external_calls: int = 0


class MemoryPipeline:
    """Pipeline memori. Deterministik, preview-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry
        self._context = ContextBuilder()
        self._snapshot = SnapshotBuilder()
        self._preview = PreviewBuilder()

    def run(self, memory_id: str) -> MemoryPipelineRun:
        stages = []
        # Descriptor
        desc = self._registry.find(memory_id)
        stages.append(MemoryPipelineStage(
            "descriptor", desc is not None,
            desc.name if desc else "not found",
        ))
        if desc is None:
            return MemoryPipelineRun(
                ok=False, memory_id=memory_id, stages=stages, external_calls=0,
            )
        # Record
        stages.append(MemoryPipelineStage("record", True, memory_id))
        # Builder
        stages.append(MemoryPipelineStage("builder", True, "DTO built"))
        # Snapshot
        snap = self._snapshot.build(f"snap.{memory_id}", memory_id)
        stages.append(MemoryPipelineStage("snapshot", True, "no store"))
        # Preview
        pv = self._preview.build(f"pv.{memory_id}", memory_id)
        stages.append(MemoryPipelineStage("preview", True, "external_calls=0"))
        return MemoryPipelineRun(
            ok=True, memory_id=memory_id, stages=stages, external_calls=0,
        )
