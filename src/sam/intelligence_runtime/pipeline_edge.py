"""Sprint 263 - Pipeline Graph: pipeline_edge."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PipelineEdge:
    """Edge graph: hubungan terarah source -> target (immutable)."""

    source: str
    target: str
    kind: str = "flow"

    def as_dict(self) -> dict:
        return {"source": self.source, "target": self.target, "kind": self.kind}
