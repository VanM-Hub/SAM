"""Knowledge Pipeline — pipeline runtime knowledge (Sprint 183).

Pipeline: Descriptor → Fact → Relation → Knowledge → Preview.
Preview-only, external_calls selalu 0, tanpa inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.knowledge_registry import KnowledgeRegistry
from ..builder.fact_builder import FactBuilder
from ..builder.relation_builder import RelationBuilder
from ..builder.preview_builder import PreviewBuilder


@dataclass(frozen=True)
class KnowledgePipelineStage:
    """Satu tahap pipeline knowledge (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class KnowledgePipelineRun:
    """Hasil pipeline knowledge (immutable)."""
    ok: bool = False
    knowledge_id: str = ""
    stages: List[KnowledgePipelineStage] = field(default_factory=list)
    external_calls: int = 0


class KnowledgePipeline:
    """Pipeline knowledge. Deterministik, preview-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry
        self._fact = FactBuilder()
        self._relation = RelationBuilder()
        self._preview = PreviewBuilder()

    def run(self, knowledge_id: str) -> KnowledgePipelineRun:
        stages = []
        # Descriptor
        desc = self._registry.find(knowledge_id)
        stages.append(KnowledgePipelineStage(
            "descriptor", desc is not None,
            desc.name if desc else "not found",
        ))
        if desc is None:
            return KnowledgePipelineRun(
                ok=False, knowledge_id=knowledge_id, stages=stages, external_calls=0,
            )
        # Fact
        fact = self._fact.build(f"fact.{knowledge_id}", knowledge_id)
        stages.append(KnowledgePipelineStage("fact", True, "no inference"))
        # Relation
        rel = self._relation.build(f"rel.{knowledge_id}", knowledge_id)
        stages.append(KnowledgePipelineStage("relation", True, "no inference"))
        # Knowledge
        stages.append(KnowledgePipelineStage("knowledge", True, knowledge_id))
        # Preview
        pv = self._preview.build(f"pv.{knowledge_id}", knowledge_id)
        stages.append(KnowledgePipelineStage("preview", True, "external_calls=0"))
        return KnowledgePipelineRun(
            ok=True, knowledge_id=knowledge_id, stages=stages, external_calls=0,
        )
