"""Audit Runtime Pipeline — pipeline integrasi audit (Sprint 219).

Pipeline final:
Mission → Agent → Skill → Workflow → Policy → Audit → Memory → Knowledge
→ Cognitive → Orchestrator → Connector → Provider → Execution Preview

Integrasi read-only — TIDAK mengubah runtime lain. Immutable audit,
preview-only, tanpa eksekusi dan tanpa penyimpanan.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.audit_registry import AuditRegistry

INTEGRATION_ROUTE = [
    "mission", "agent", "skill", "workflow", "policy", "audit", "memory",
    "knowledge", "cognitive", "orchestrator", "connector", "provider",
]


@dataclass(frozen=True)
class AuditIntegrationStage:
    """Satu tahap pipeline integrasi (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class AuditRuntimePipelineRun:
    """Hasil pipeline integrasi (immutable)."""
    ok: bool = False
    audit_id: str = ""
    stages: List[AuditIntegrationStage] = field(default_factory=list)
    external_calls: int = 0


class AuditRuntimePipeline:
    """Pipeline integrasi audit. Read-only, deterministik, preview-only."""

    def __init__(self, registry: AuditRegistry) -> None:
        self._registry = registry

    def run(self, audit_id: str) -> AuditRuntimePipelineRun:
        stages = []
        for name in ["mission", "agent", "skill", "workflow", "policy"]:
            stages.append(AuditIntegrationStage(name, True, "read-only"))
        exists = self._registry.exists(audit_id)
        stages.append(AuditIntegrationStage(
            "audit", exists, "found" if exists else "not found",
        ))
        if not exists:
            return AuditRuntimePipelineRun(
                ok=False, audit_id=audit_id, stages=stages, external_calls=0,
            )
        for name in ["memory", "knowledge", "cognitive", "orchestrator",
                     "connector", "provider"]:
            stages.append(AuditIntegrationStage(name, True, "read-only"))
        stages.append(AuditIntegrationStage(
            "execution_preview", True, "external_calls=0",
        ))
        return AuditRuntimePipelineRun(
            ok=True, audit_id=audit_id, stages=stages, external_calls=0,
        )

    def route(self) -> List[str]:
        return list(INTEGRATION_ROUTE)
