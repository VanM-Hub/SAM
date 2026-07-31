"""Sprint 265 - Intelligence Runtime: orchestrator utama (preview-only, sync, tanpa inference/LLM).

Pipeline: Registry -> Graph -> Context -> Validation -> Assembly -> Report.
Semua artefak immutable & deterministik; tidak ada IO/network/thread.
"""
from __future__ import annotations

from typing import Optional

from .context_builder import ContextBuilder
from .context_report import ContextReport
from .context_snapshot import ContextSnapshot
from .context_validator import ContextValidator
from .pipeline_builder import PipelineBuilder
from .pipeline_validator import PipelineValidator
from .runtime_pipeline import RuntimePipeline
from .runtime_registry import RuntimeRegistry
from .runtime_report import RuntimeReport
from .runtime_session import RuntimeSession


class IntelligenceRuntime:
    """Intelligence Runtime: menyatukan registry, graph, context, report.

    Class service (bukan DTO). Setelah konstruksi, atribut bersifat read-only
    (immutable contract) dan method tidak mengubah state internal.
    """

    def __init__(
        self,
        registry: RuntimeRegistry,
        validator: PipelineValidator = PipelineValidator(),
        context_validator: Optional[ContextValidator] = None,
        required_sections: tuple = (
            "Mission", "Agent", "Workflow", "Skill", "Memory", "Knowledge",
            "Policy", "Audit", "Artifact", "Model", "Provider", "Execution",
        ),
    ):
        self._registry = registry
        self._validator = validator
        self._context_validator = context_validator
        self._required_sections = tuple(required_sections)
        self._locked = True

    def __setattr__(self, name, value):
        if getattr(self, "_locked", False):
            raise AttributeError(f"IntelligenceRuntime is immutable: {name}")
        super().__setattr__(name, value)

    @property
    def registry(self) -> RuntimeRegistry:
        return self._registry

    @property
    def validator(self) -> PipelineValidator:
        return self._validator

    @property
    def context_validator(self) -> Optional[ContextValidator]:
        return self._context_validator

    @property
    def required_sections(self) -> tuple:
        return self._required_sections

    def run(
        self,
        context_builder: Optional[ContextBuilder] = None,
        stages: Optional[tuple] = None,
    ) -> RuntimeSession:
        """Jalankan pipeline penuh secara sinkron & deterministic.

        - Registry: baca referensi runtime.
        - Graph: susun graph — tidak menjalankan runtime.
        - Context: rakit snapshot konteks.
        - Validation: validasi graph (DAG) + kelengkapan konteks.
        - Assembly: hasil akhir.
        - Report: laporan.
        """
        pipe = RuntimePipeline()
        resolved_stages = tuple(stages) if stages is not None else pipe.stages

        # Registry
        registry_artifact = self._registry.as_dict()

        # Graph (dari nama runtime yang terdaftar)
        names = tuple(r.descriptor.name for r in self._registry.refs)
        graph = PipelineBuilder.build(names)
        graph_issues = self._validator.validate(graph)
        graph_ok = len(graph_issues) == 0

        # Context
        if context_builder is None:
            b = ContextBuilder.create()
            for s in self._required_sections:
                b = b.add(s, {"from_registry": True})
            ctx = b.build()
        else:
            ctx = context_builder.build()
        ctx_issues = self._validate_context(ctx)

        # Assembly + Report
        report = ContextReport().build(copy_snapshot(ctx))
        artifacts = {
            "registry": registry_artifact,
            "graph": graph.as_dict(),
            "graph_valid": graph_ok,
            "context": ctx.as_dict(),
            "context_issues": [i.__dict__ for i in ctx_issues],
            "report": report,
        }

        completed = graph_ok and len(ctx_issues) == 0
        full = RuntimeReport(stages=resolved_stages, artifacts=artifacts)
        return RuntimeSession(report=full, completed=completed)

    def _validate_context(self, ctx: ContextSnapshot):
        validator = self._context_validator
        if validator is None:
            validator = ContextValidator(required=tuple(self._required_sections))
        return validator.validate(ctx)

    def as_dict(self) -> dict:
        return {
            "registry_count": len(self._registry),
            "pipeline": list(RuntimePipeline().stages),
            "preview_only": True,
            "inference": False,
            "llm": False,
        }


def copy_snapshot(snap: ContextSnapshot) -> ContextSnapshot:
    """Kembalikan salinan snapshot (immutable, aman dibagikan)."""
    return ContextSnapshot(
        sections={k: dict(v) for k, v in snap.sections.items()},
        order=snap.order,
    )
