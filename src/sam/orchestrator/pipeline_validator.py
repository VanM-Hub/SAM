# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 126 - Pipeline Builder: pipeline_validator.

Validates a built pipeline for well-formedness.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .pipeline_builder import BuiltPipeline


@dataclass(frozen=True)
class PipelineValidationIssue:
    message: str


@dataclass(frozen=True)
class PipelineValidationReport:
    valid: bool
    issues: Tuple[PipelineValidationIssue, ...] = field(default_factory=tuple)

    @property
    def issue_count(self) -> int:
        return len(self.issues)


class PipelineValidator:
    """Validates a built pipeline."""

    def validate(self, pipeline: BuiltPipeline) -> PipelineValidationReport:
        issues = []
        for idx, stage in enumerate(pipeline.stages):
            if stage.order != idx:
                issues.append(
                    PipelineValidationIssue("stage {0} order mismatch".format(stage.stage_id))
                )
            if not stage.runtime_id:
                issues.append(PipelineValidationIssue("empty runtime in stage"))
        return PipelineValidationReport(valid=not issues, issues=tuple(issues))
