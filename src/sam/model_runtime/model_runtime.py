"""Model Runtime — runtime utama model (Sprint 246).

Program B — Model Runtime Integration.
Mengorkestrasi pipeline. Read-only, preview-only, no-network.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .model_descriptor import ModelDescriptor
from .model_request import ModelRequest
from .model_pipeline import ModelPipeline, ModelPipelineLog
from .model_report import ModelReport
from .model_registry import ModelRegistry
from .model_validator import ModelValidator
from .chat_preview import ChatPreviewEngine


@dataclass(frozen=True)
class ModelRuntimeResult:
    """Hasil runtime model (immutable)."""
    runtime_id: str
    report: ModelReport
    preview_only: bool = True
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "report": self.report.as_dict(),
            "preview_only": self.preview_only,
            "external_calls": self.external_calls,
        }


class ModelRuntime:
    """Runtime model. Menjalankan pipeline secara read-only."""

    def __init__(
        self,
        registry: ModelRegistry | None = None,
        pipeline: ModelPipeline | None = None,
        runtime_id: str = "model-runtime",
    ) -> None:
        self._registry = registry or ModelRegistry()
        self._pipeline = pipeline or ModelPipeline(
            validator=ModelValidator(),
            preview_provider=ChatPreviewEngine(),
        )
        self._runtime_id = runtime_id

    @property
    def runtime_id(self) -> str:
        return self._runtime_id

    def registry(self) -> ModelRegistry:
        return self._registry

    def run(self, descriptor: ModelDescriptor, request: ModelRequest) -> ModelRuntimeResult:
        report = self._pipeline.run(descriptor, request)
        return ModelRuntimeResult(
            runtime_id=self._runtime_id,
            report=report,
            preview_only=True,
            external_calls=0,
        )

    def pipeline_log(self) -> ModelPipelineLog:
        return self._pipeline.log()
