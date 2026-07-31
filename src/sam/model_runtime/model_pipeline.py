"""Model Pipeline — pipeline model (Sprint 246).

Program B — Model Runtime Integration.
Pipeline: Descriptor -> Request -> Validation -> Preview -> Report.
Semua tahap deterministik, no-network, preview-only.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List, Optional

from .model_descriptor import ModelDescriptor
from .model_request import ModelRequest
from .model_validator import ModelValidationResult
from .model_report import ModelReport, ModelReportBuilder


@dataclass(frozen=True)
class ModelPipelineStage:
    """Satu tahap pipeline (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""
    external_calls: int = 0

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "ok": self.ok,
            "detail": self.detail,
            "external_calls": self.external_calls,
        }


@dataclass(frozen=True)
class ModelPipelineLog:
    """Log tahap-tahap pipeline (immutable)."""
    stages: List[ModelPipelineStage] = field(default_factory=list)

    def as_dict(self) -> dict:
        return {"stages": [s.as_dict() for s in self.stages]}


class ModelPipeline:
    """Pipeline model: Descriptor -> Request -> Validation -> Preview -> Report.

    Read-only pipeline; tidak ada eksekusi/network.
    """

    STAGES = ("descriptor", "request", "validation", "preview", "report")

    def __init__(
        self,
        validator=None,
        preview_provider=None,
        report_builder: ModelReportBuilder | None = None,
    ) -> None:
        from .model_validator import ModelValidator
        from .chat_preview import ChatPreviewEngine
        self._validator = validator or ModelValidator()
        self._preview = preview_provider or ChatPreviewEngine()
        self._report_builder = report_builder or ModelReportBuilder()
        self._log: List[ModelPipelineStage] = []

    def run(self, descriptor: ModelDescriptor, request: ModelRequest) -> ModelReport:
        self._log = []
        # 1. Descriptor
        self._log.append(ModelPipelineStage("descriptor", bool(descriptor.id),
                                            detail=f"descriptor={descriptor.id}"))
        # 2. Request
        self._log.append(ModelPipelineStage("request", bool(request.request_id),
                                            detail=f"request={request.request_id}"))
        # 3. Validation
        validation = self._validator.validate_request(request)
        self._log.append(ModelPipelineStage(
            "validation", validation.valid,
            detail="; ".join(validation.errors) if validation.errors else "valid"))
        if not validation.valid:
            self._log.append(ModelPipelineStage("preview", False, detail="blocked"))
            self._log.append(ModelPipelineStage("report", True, detail="error report"))
            return self._report_builder.failed(request.request_id, validation.errors)
        # 4. Preview
        preview = self._preview.preview(request)
        self._log.append(ModelPipelineStage("preview", True, detail=f"tokens={preview.estimated_tokens}"))
        # 5. Report
        report = self._report_builder.success(request, preview)
        self._log.append(ModelPipelineStage("report", True, detail=f"report={report.report_id}"))
        return report

    def log(self) -> ModelPipelineLog:
        return ModelPipelineLog(stages=list(self._log))
