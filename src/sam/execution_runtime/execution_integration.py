"""Execution Integration (Sprint 259).

Program C - Real Execution Runtime.
Pipeline akhir: Mission -> Workflow -> Policy -> Memory -> Knowledge ->
Cognitive -> Orchestrator -> Connector -> Provider -> Model Runtime ->
Approval -> Execution Runtime -> Artifact.

Semua bridge read-only (tidak mengubah subsystem lain). Eksekusi nyata
hanya pada tahap execution_runtime, dan hanya bila approval valid.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .execution_runtime_registry import (
    ExecutionRuntimeRegistry, RuntimeEntry, PIPELINE_ORDER,
)
from .execution_runtime import ExecutionRuntime, ExecutionOutcome
from .execution_certifier import ExecutionCertifier
from .execution_descriptor import ExecutionDescriptor
from .execution_request import ExecutionRequest
from .approval_gate import ApprovalGate


@dataclass(frozen=True)
class IntegrationStage:
    """Satu tahap integrasi (immutable)."""
    name: str
    reached: bool = True
    bridge: str = "read-only"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {"name": self.name, "reached": self.reached,
                "bridge": self.bridge, "external_calls": self.external_calls}


@dataclass(frozen=True)
class ExecutionIntegrationResult:
    """Hasil integrasi (immutable)."""
    integration_id: str
    stages: List[IntegrationStage] = field(default_factory=list)
    outcome: Optional[ExecutionOutcome] = None
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "integration_id": self.integration_id,
            "stages": [s.as_dict() for s in self.stages],
            "outcome": self.outcome.as_dict() if self.outcome else None,
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ExecutionIntegration:
    """Integrasi execution ke pipeline akhir. Read-only orchestrator."""

    def __init__(self, registry: ExecutionRuntimeRegistry | None = None,
                 runtime: ExecutionRuntime | None = None,
                 gate: ApprovalGate | None = None,
                 certifier: ExecutionCertifier | None = None) -> None:
        self._registry = registry or ExecutionRuntimeRegistry()
        self._runtime = runtime or ExecutionRuntime()
        self._registry.register_execution_runtime(self._runtime)
        self._gate = gate or ApprovalGate()
        self._certifier = certifier or ExecutionCertifier()

    @property
    def registry(self) -> ExecutionRuntimeRegistry:
        return self._registry

    def pipeline(self) -> List[str]:
        return list(PIPELINE_ORDER)

    def run(self, descriptor: ExecutionDescriptor, request: ExecutionRequest) -> ExecutionIntegrationResult:
        stages = [IntegrationStage(n, True, "read-only", 0) for n in PIPELINE_ORDER]
        outcome = None
        if request.mode == "execute" and self._gate.may_execute(request):
            outcome = self._runtime.run(f"int-{descriptor.id}", request)
            stages.append(IntegrationStage("execution_runtime", True, "own", outcome.external_calls))
        return ExecutionIntegrationResult(
            integration_id=f"int-{descriptor.id}",
            stages=stages,
            outcome=outcome,
            # preview_only = tidak ada eksekusi nyata yang terjadi
            preview_only=(outcome is None),
            external_calls=outcome.external_calls if outcome else 0,
        )

    def certify(self, manifest) -> object:
        return self._certifier.certify(manifest)
