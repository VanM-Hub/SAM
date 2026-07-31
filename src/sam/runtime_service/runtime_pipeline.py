"""RuntimePipeline (Sprint 271).

Program D - Runtime Services & Deployment.
Pipeline akhir SAM:
Mission -> Workflow -> Policy -> Agent -> Skill -> Memory -> Knowledge
-> Cognitive -> Orchestrator -> Connector -> Provider -> Execution Runtime
-> Runtime Service -> External Provider
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

PIPELINE_STAGES = (
    "Mission",
    "Workflow",
    "Policy",
    "Agent",
    "Skill",
    "Memory",
    "Knowledge",
    "Cognitive",
    "Orchestrator",
    "Connector",
    "Provider",
    "Execution Runtime",
    "Runtime Service",
    "External Provider",
)


@dataclass(frozen=True)
class PipelineStageResult:
    """Hasil tahap pipeline (immutable)."""
    stage: str
    ok: bool = True
    detail: str = ""


class RuntimePipeline:
    """Pipeline runtime (sync, deterministic)."""

    def __init__(self, stages: List[str] = None) -> None:
        self._stages = list(stages or PIPELINE_STAGES)
        self._results: List[PipelineStageResult] = []

    @property
    def stages(self) -> tuple:
        return tuple(self._stages)

    def validate(self) -> bool:
        """Cek urutan pipeline sah & runtime service hadir."""
        return ("Execution Runtime" in self._stages
                and "Runtime Service" in self._stages
                and self._stages.index("Runtime Service")
                == self._stages.index("Execution Runtime") + 1)

    def run(self) -> List[PipelineStageResult]:
        self._results = [
            PipelineStageResult(stage=s) for s in self._stages
        ]
        return list(self._results)

    def results(self) -> List[PipelineStageResult]:
        return list(self._results)

    def all_ok(self) -> bool:
        return all(r.ok for r in self._results)

    def count(self) -> int:
        return len(self._stages)
