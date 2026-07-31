"""Skill Runtime Pipeline — pipeline integrasi (Sprint 171).

Pipeline final:
Mission → Agent → Skill → Orchestrator → Connector → Provider → Execution Preview

Integrasi read-only. TIDAK mengubah runtime lain. Preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry

# Urutan pipeline integrasi skill (read-only)
INTEGRATION_ROUTE = [
    "mission", "agent", "skill", "orchestrator", "connector", "provider",
]


@dataclass(frozen=True)
class IntegrationStage:
    """Satu tahap pipeline integrasi (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class SkillRuntimePipelineRun:
    """Hasil pipeline integrasi (immutable)."""
    ok: bool = False
    skill_id: str = ""
    stages: List[IntegrationStage] = field(default_factory=list)
    external_calls: int = 0


class SkillRuntimePipeline:
    """Pipeline integrasi skill. Read-only, deterministik, preview-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry

    def run(self, skill_id: str) -> SkillRuntimePipelineRun:
        stages = []
        # Mission
        stages.append(IntegrationStage("mission", True, "read-only"))
        # Agent
        stages.append(IntegrationStage("agent", True, "read-only"))
        # Skill
        exists = self._registry.exists(skill_id)
        stages.append(IntegrationStage(
            "skill", exists, "found" if exists else "not found",
        ))
        if not exists:
            return SkillRuntimePipelineRun(
                ok=False, skill_id=skill_id, stages=stages, external_calls=0,
            )
        # Orchestrator / Connector / Provider
        stages.append(IntegrationStage("orchestrator", True, "read-only"))
        stages.append(IntegrationStage("connector", True, "read-only"))
        stages.append(IntegrationStage("provider", True, "read-only"))
        # Execution Preview
        stages.append(IntegrationStage(
            "execution_preview", True, "external_calls=0",
        ))
        return SkillRuntimePipelineRun(
            ok=True, skill_id=skill_id, stages=stages, external_calls=0,
        )

    def route(self) -> List[str]:
        return list(INTEGRATION_ROUTE)
