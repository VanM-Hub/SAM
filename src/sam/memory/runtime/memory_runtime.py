"""Memory Runtime — engine runtime memori (Sprint 175).

Pipeline: Descriptor → Record → Builder → Snapshot → Preview.
Preview-only, external_calls selalu 0, tidak menyimpan apa pun.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Optional

from ..foundation.memory_registry import MemoryRegistry
from ..builder.memory_builder import MemoryBuilder


@dataclass(frozen=True)
class MemoryRunResult:
    """Hasil menjalankan pipeline memori (immutable)."""
    memory_id: str
    ok: bool = False
    steps: int = 0
    external_calls: int = 0
    detail: str = ""


class MemoryRuntime:
    """Runtime memori. Pipeline preview-only."""

    RUNTIME_VERSION = "1.0.0"

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry
        self._builder = MemoryBuilder()

    def pipeline(self, memory_id: str) -> MemoryRunResult:
        if not self._registry.exists(memory_id):
            return MemoryRunResult(
                memory_id=memory_id, ok=False, detail="memory not registered"
            )
        descriptor = self._registry.find(memory_id)
        built = self._builder.build(memory_id, name=descriptor.name)
        if not built.valid:
            return MemoryRunResult(
                memory_id=memory_id, ok=False, detail="build failed"
            )
        return MemoryRunResult(
            memory_id=memory_id, ok=True, steps=1, external_calls=0,
            detail="preview pipeline ready",
        )

    def run(self, memory_id: str) -> MemoryRunResult:
        return self.pipeline(memory_id)

    @property
    def registry(self) -> MemoryRegistry:
        return self._registry
