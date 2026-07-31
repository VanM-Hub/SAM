"""Policy Pipeline — pipeline policy (Sprint 207)."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from ..foundation.policy_registry import PolicyRegistry


@dataclass(frozen=True)
class PolicyPipelineStage:
    """Satu tahap pipeline (immutable)."""
    name: str
    ok: bool = True
    detail: str = ""


@dataclass(frozen=True)
class PolicyPipelineRun:
    """Hasil pipeline (immutable)."""
    ok: bool = False
    stages: List[PolicyPipelineStage] = field(default_factory=list)
    external_calls: int = 0


class PolicyPipeline:
    """Pipeline: Descriptor → Policy → Builder → Preview."""

    STAGES = ["descriptor", "policy", "builder", "preview"]

    def __init__(self, registry: PolicyRegistry) -> None:
        self._registry = registry

    def stages(self) -> List[str]:
        return list(self.STAGES)

    def run(self, policy_id: str) -> PolicyPipelineRun:
        ok = self._registry.exists(policy_id)
        stages = [PolicyPipelineStage(
            "descriptor", ok, "found" if ok else "not found",
        )]
        if not ok:
            return PolicyPipelineRun(ok=False, stages=stages, external_calls=0)
        for name in ["policy", "builder", "preview"]:
            stages.append(PolicyPipelineStage(name, True, "read-only"))
        return PolicyPipelineRun(ok=True, stages=stages, external_calls=0)
