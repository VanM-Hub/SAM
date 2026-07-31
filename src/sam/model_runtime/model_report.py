"""Model Report — laporan pipeline model (Sprint 246).

Program B — Model Runtime Integration.
Laporan deterministik, preview-only, external_calls=0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .model_request import ModelRequest
from .chat_preview import ChatPreview


@dataclass(frozen=True)
class ModelReport:
    """Laporan model (immutable)."""
    report_id: str
    request_id: str = ""
    ok: bool = True
    stages_completed: int = 0
    preview: object = None
    errors: List[str] = field(default_factory=list)
    external_calls: int = 0

    def as_dict(self) -> dict:
        preview_dict = self.preview.as_dict() if hasattr(self.preview, "as_dict") else self.preview
        return {
            "report_id": self.report_id,
            "request_id": self.request_id,
            "ok": self.ok,
            "stages_completed": self.stages_completed,
            "preview": preview_dict,
            "errors": list(self.errors),
            "external_calls": self.external_calls,
        }


class ModelReportBuilder:
    """Builder deterministik untuk ModelReport."""

    def success(self, request: ModelRequest, preview: ChatPreview) -> ModelReport:
        return ModelReport(
            report_id=f"rep-{request.request_id}",
            request_id=request.request_id,
            ok=True,
            stages_completed=5,
            preview=preview,
            errors=[],
            external_calls=0,
        )

    def failed(self, request_id: str, errors: List[str]) -> ModelReport:
        return ModelReport(
            report_id=f"rep-{request_id}",
            request_id=request_id,
            ok=False,
            stages_completed=3,
            preview=None,
            errors=list(errors),
            external_calls=0,
        )
