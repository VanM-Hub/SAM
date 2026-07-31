"""Memory Runtime Pipeline — pipeline integrasi (Sprint 179).

Pipeline final:
Mission → Agent → Skill → Memory → Orchestrator → Connector → Provider → Execution Preview

Integrasi read-only. TIDAK mengubah runtime lain. Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.memory_registry import MemoryRegistry

INTEGRATION_ROUTE = [
    "mission", "agent", "skill", "memory",
    "orchestrator", "connector", "provider",
]


@dataclass(frozen=True)
class MemoryIntegrationStage:
    """Satu tahap pipeline integrasi (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class MemoryRuntimePipelineRun:
    """Hasil pipeline integrasi (immutable)."""
    ok: bool = False
    memory_id: str = ""
    stages: List[MemoryIntegrationStage] = field(default_factory=list)
    external_calls: int = 0


class MemoryRuntimePipeline:
    """Pipeline integrasi memori. Read-only, deterministik, preview-only."""

    def __init__(self, registry: MemoryRegistry) -> None:
        self._registry = registry

    def run(self, memory_id: str) -> MemoryRuntimePipelineRun:
        stages = []
        # Mission / Agent / Skill
        for name in ["mission", "agent", "skill"]:
            stages.append(MemoryIntegrationStage(name, True, "read-only"))
        # Memory
        exists = self._registry.exists(memory_id)
        stages.append(MemoryIntegrationStage(
            "memory", exists, "found" if exists else "not found",
        ))
        if not exists:
            return MemoryRuntimePipelineRun(
                ok=False, memory_id=memory_id, stages=stages, external_calls=0,
            )
        # Orchestrator / Connector / Provider
        for name in ["orchestrator", "connector", "provider"]:
            stages.append(MemoryIntegrationStage(name, True, "read-only"))
        # Execution Preview
        stages.append(MemoryIntegrationStage(
            "execution_preview", True, "external_calls=0",
        ))
        return MemoryRuntimePipelineRun(
            ok=True, memory_id=memory_id, stages=stages, external_calls=0,
        )

    def route(self) -> List[str]:
        return list(INTEGRATION_ROUTE)
