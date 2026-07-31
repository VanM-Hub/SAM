"""Knowledge Runtime Pipeline — pipeline integrasi (Sprint 187).

Pipeline final:
Mission → Agent → Skill → Memory → Knowledge → Orchestrator → Connector → Provider → Execution Preview

Integrasi read-only. TIDAK mengubah runtime lain. Preview-only, tanpa inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.knowledge_registry import KnowledgeRegistry

INTEGRATION_ROUTE = [
    "mission", "agent", "skill", "memory", "knowledge",
    "orchestrator", "connector", "provider",
]


@dataclass(frozen=True)
class KnowledgeIntegrationStage:
    """Satu tahap pipeline integrasi (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class KnowledgeRuntimePipelineRun:
    """Hasil pipeline integrasi (immutable)."""
    ok: bool = False
    knowledge_id: str = ""
    stages: List[KnowledgeIntegrationStage] = field(default_factory=list)
    external_calls: int = 0


class KnowledgeRuntimePipeline:
    """Pipeline integrasi knowledge. Read-only, deterministik, preview-only."""

    def __init__(self, registry: KnowledgeRegistry) -> None:
        self._registry = registry

    def run(self, knowledge_id: str) -> KnowledgeRuntimePipelineRun:
        stages = []
        # Mission / Agent / Skill / Memory
        for name in ["mission", "agent", "skill", "memory"]:
            stages.append(KnowledgeIntegrationStage(name, True, "read-only"))
        # Knowledge
        exists = self._registry.exists(knowledge_id)
        stages.append(KnowledgeIntegrationStage(
            "knowledge", exists, "found" if exists else "not found",
        ))
        if not exists:
            return KnowledgeRuntimePipelineRun(
                ok=False, knowledge_id=knowledge_id, stages=stages, external_calls=0,
            )
        # Orchestrator / Connector / Provider
        for name in ["orchestrator", "connector", "provider"]:
            stages.append(KnowledgeIntegrationStage(name, True, "read-only"))
        # Execution Preview
        stages.append(KnowledgeIntegrationStage(
            "execution_preview", True, "external_calls=0",
        ))
        return KnowledgeRuntimePipelineRun(
            ok=True, knowledge_id=knowledge_id, stages=stages, external_calls=0,
        )

    def route(self) -> List[str]:
        return list(INTEGRATION_ROUTE)
