"""Cognitive Runtime Pipeline — pipeline integrasi (Sprint 195).

Pipeline final:
Mission → Agent → Skill → Memory → Knowledge → Cognitive
→ Orchestrator → Connector → Provider → Execution Preview

Integrasi read-only — TIDAK mengubah runtime lain. Preview-only, tanpa inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.cognitive_registry import CognitiveRegistry

INTEGRATION_ROUTE = [
    "mission", "agent", "skill", "memory", "knowledge", "cognitive",
    "orchestrator", "connector", "provider",
]


@dataclass(frozen=True)
class CognitiveIntegrationStage:
    """Satu tahap pipeline integrasi (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class CognitiveRuntimePipelineRun:
    """Hasil pipeline integrasi (immutable)."""
    ok: bool = False
    cognitive_id: str = ""
    stages: List[CognitiveIntegrationStage] = field(default_factory=list)
    external_calls: int = 0


class CognitiveRuntimePipeline:
    """Pipeline integrasi kognitif. Read-only, deterministik, preview-only."""

    def __init__(self, registry: CognitiveRegistry) -> None:
        self._registry = registry

    def run(self, cognitive_id: str) -> CognitiveRuntimePipelineRun:
        stages = []
        for name in ["mission", "agent", "skill", "memory", "knowledge"]:
            stages.append(CognitiveIntegrationStage(name, True, "read-only"))
        exists = self._registry.exists(cognitive_id)
        stages.append(CognitiveIntegrationStage(
            "cognitive", exists, "found" if exists else "not found",
        ))
        if not exists:
            return CognitiveRuntimePipelineRun(
                ok=False, cognitive_id=cognitive_id, stages=stages, external_calls=0,
            )
        for name in ["orchestrator", "connector", "provider"]:
            stages.append(CognitiveIntegrationStage(name, True, "read-only"))
        stages.append(CognitiveIntegrationStage(
            "execution_preview", True, "external_calls=0",
        ))
        return CognitiveRuntimePipelineRun(
            ok=True, cognitive_id=cognitive_id, stages=stages, external_calls=0,
        )

    def route(self) -> List[str]:
        return list(INTEGRATION_ROUTE)
