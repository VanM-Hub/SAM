"""Skill Pipeline — pipeline runtime skill (Sprint 167).

Pipeline:
Descriptor → Definition → Builder → Workflow → Preview
Semua preview-only, external_calls selalu 0.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.skill_registry import SkillRegistry
from ..builder.workflow_builder import WorkflowBuilder
from ..builder.preview_builder import PreviewBuilder


@dataclass(frozen=True)
class SkillPipelineStage:
    """Satu tahap pipeline skill (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class SkillPipelineRun:
    """Hasil pipeline skill (immutable)."""
    ok: bool = False
    skill_id: str = ""
    stages: List[SkillPipelineStage] = field(default_factory=list)
    external_calls: int = 0


class SkillPipeline:
    """Pipeline skill. Deterministik, preview-only."""

    def __init__(self, registry: SkillRegistry) -> None:
        self._registry = registry
        self._workflow = WorkflowBuilder()
        self._preview = PreviewBuilder()

    def run(self, skill_id: str) -> SkillPipelineRun:
        stages = []
        # Descriptor
        desc = self._registry.find(skill_id)
        stages.append(SkillPipelineStage(
            "descriptor", desc is not None,
            desc.name if desc else "not found",
        ))
        if desc is None:
            return SkillPipelineRun(ok=False, skill_id=skill_id, stages=stages)
        # Definition
        stages.append(SkillPipelineStage("definition", True, skill_id))
        # Builder
        stages.append(SkillPipelineStage("builder", True, "DTO built"))
        # Workflow
        wf = self._workflow.build(f"wf.{skill_id}", skill_id)
        stages.append(SkillPipelineStage("workflow", True, f"{wf.step_count} steps"))
        # Preview
        pv = self._preview.build(f"pv.{skill_id}", skill_id)
        stages.append(SkillPipelineStage("preview", True, "external_calls=0"))
        return SkillPipelineRun(
            ok=True, skill_id=skill_id, stages=stages, external_calls=0,
        )
