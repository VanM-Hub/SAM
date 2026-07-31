"""Model Integration — integrasi model ke pipeline akhir (Sprint 249).

Program B — Model Runtime Integration.
Pipeline akhir: Mission -> Agent -> Workflow -> Memory -> Knowledge ->
Cognitive -> Policy -> Audit -> Artifact -> Connector -> Provider ->
Model Runtime -> Execution Preview.

Semua bridge read-only; preview-only; external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .runtime_registry import RuntimeRegistry, RUNTIME_PIPELINE_ORDER
from .model_runtime import ModelRuntime
from .model_certifier import ModelCertifier
from .model_descriptor import ModelDescriptor
from .model_request import ModelRequest


@dataclass(frozen=True)
class IntegrationStage:
    """Satu tahap integrasi (immutable)."""
    name: str
    reached: bool = True
    bridge: str = "read-only"
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "reached": self.reached,
            "bridge": self.bridge,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class ModelIntegrationResult:
    """Hasil integrasi (immutable)."""
    integration_id: str
    stages: List[IntegrationStage] = field(default_factory=list)
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "integration_id": self.integration_id,
            "stages": [s.as_dict() for s in self.stages],
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ModelIntegration:
    """Integrasi model ke pipeline akhir. Read-only orchestrator."""

    def __init__(
        self,
        registry: RuntimeRegistry | None = None,
        runtime: ModelRuntime | None = None,
        certifier: ModelCertifier | None = None,
    ) -> None:
        self._registry = registry or RuntimeRegistry()
        self._runtime = runtime or ModelRuntime()
        self._registry.register_model_runtime(self._runtime)
        self._certifier = certifier or ModelCertifier()

    @property
    def registry(self) -> RuntimeRegistry:
        return self._registry

    def pipeline(self) -> List[str]:
        return list(RUNTIME_PIPELINE_ORDER)

    def run(self, descriptor: ModelDescriptor, request: ModelRequest) -> ModelIntegrationResult:
        stages = []
        for stage in RUNTIME_PIPELINE_ORDER:
            stages.append(IntegrationStage(
                name=stage, reached=True, bridge="read-only", external_calls=0))
        # Model runtime stage menjalankan pipeline-nya
        self._runtime.run(descriptor, request)
        return ModelIntegrationResult(
            integration_id=f"int-{descriptor.id}",
            stages=stages,
            preview_only=True,
            external_calls=0,
        )

    def certify(self, manifest) -> object:
        return self._certifier.certify(manifest)
