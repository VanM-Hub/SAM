# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 132 - Runtime Engine: conversation_engine.

Read-only conversation bridge for the runtime engine.
"""
from __future__ import annotations

from typing import Dict, Tuple

from .runtime_engine import RuntimeEngine
from .runtime_pipeline import RuntimePipeline
from .runtime_report import RuntimeReport


class ConversationEngineBridge:
    """Read-only bridge exposing engine readiness."""

    def __init__(self, engine: RuntimeEngine) -> None:
        self._engine = engine

    def report(self, pipeline_id: str, order: Tuple[str, ...]) -> RuntimeReport:
        pipeline = self._engine.build_pipeline(pipeline_id, order)
        return self._engine.report(pipeline)

    def stages(self, report: RuntimeReport) -> int:
        return report.snapshot.pipeline.stage_count

    def summary(self, report: RuntimeReport) -> Dict[str, object]:
        return {
            "ready": report.ok,
            "stages": report.snapshot.pipeline.stage_count,
            "engine": self._engine.ENGINE_VERSION,
        }
