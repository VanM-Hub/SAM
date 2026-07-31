"""Policy Runtime Pipeline — pipeline integrasi (Sprint 211).

Pipeline final:
Mission → Agent → Skill → Workflow → Policy → Memory → Knowledge → Cognitive
→ Orchestrator → Connector → Provider → Execution Preview

Integrasi read-only — TIDAK mengubah runtime lain. Preview-only, tanpa inferensi.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.policy_registry import PolicyRegistry

INTEGRATION_ROUTE = [
    "mission", "agent", "skill", "workflow", "policy", "memory", "knowledge",
    "cognitive", "orchestrator", "connector", "provider",
]


@dataclass(frozen=True)
class PolicyIntegrationStage:
    """Satu tahap pipeline integrasi (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class PolicyRuntimePipelineRun:
    """Hasil pipeline integrasi (immutable)."""
    ok: bool = False
    policy_id: str = ""
    stages: List[PolicyIntegrationStage] = field(default_factory=list)
    external_calls: int = 0


class PolicyRuntimePipeline:
    """Pipeline integrasi policy. Read-only, deterministik, preview-only."""

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def run(self, policy_id: str) -> PolicyRuntimePipelineRun:
        stages = []
        for name in ["mission", "agent", "skill", "workflow"]:
            stages.append(PolicyIntegrationStage(name, True, "read-only"))
        exists = self._registry.exists(policy_id)
        stages.append(PolicyIntegrationStage(
            "policy", exists, "found" if exists else "not found",
        ))
        if not exists:
            return PolicyRuntimePipelineRun(
                ok=False, policy_id=policy_id, stages=stages, external_calls=0,
            )
        for name in ["memory", "knowledge", "cognitive", "orchestrator",
                     "connector", "provider"]:
            stages.append(PolicyIntegrationStage(name, True, "read-only"))
        stages.append(PolicyIntegrationStage(
            "execution_preview", True, "external_calls=0",
        ))
        return PolicyRuntimePipelineRun(
            ok=True, policy_id=policy_id, stages=stages, external_calls=0,
        )

    def route(self) -> List[str]:
        return list(INTEGRATION_ROUTE)
