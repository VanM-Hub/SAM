"""Knowledge Runtime — engine runtime knowledge (Sprint 183).

Pipeline: Descriptor → Fact → Relation → Knowledge → Preview.
Preview-only, external_calls selalu 0. Tanpa inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass, field

from ..foundation.knowledge_registry import KnowledgeRegistry
from ..builder.knowledge_builder import KnowledgeBuilder


@dataclass(frozen=True)
class KnowledgeRunResult:
    """Hasil menjalankan pipeline knowledge (immutable)."""
    knowledge_id: str
    ok: bool = False
    steps: int = 0
    external_calls: int = 0
    detail: str = ""


class KnowledgeRuntime:
    """Runtime knowledge. Pipeline preview-only."""

    RUNTIME_VERSION = "1.0.0"

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry
        self._builder = KnowledgeBuilder()

    def pipeline(self, knowledge_id: str) -> KnowledgeRunResult:
        if not self._registry.exists(knowledge_id):
            return KnowledgeRunResult(
                knowledge_id=knowledge_id, ok=False, detail="knowledge not registered"
            )
        descriptor = self._registry.find(knowledge_id)
        built = self._builder.build(knowledge_id, name=descriptor.name)
        if not built.valid:
            return KnowledgeRunResult(
                knowledge_id=knowledge_id, ok=False, detail="build failed"
            )
        return KnowledgeRunResult(
            knowledge_id=knowledge_id, ok=True, steps=1, external_calls=0,
            detail="preview pipeline ready, no inference",
        )

    def run(self, knowledge_id: str) -> KnowledgeRunResult:
        return self.pipeline(knowledge_id)

    @property
    def registry(self) -> KnowledgeRegistry:
        return self._registry
