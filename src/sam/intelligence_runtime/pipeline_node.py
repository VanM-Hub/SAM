"""Sprint 263 - Pipeline Graph: pipeline_node."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class PipelineNode:
    """Node graph: representasi immutable sebuah tahap pipeline."""

    name: str
    kind: str = "stage"
    attributes: Dict[str, object] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "name": self.name,
            "kind": self.kind,
            "attributes": dict(self.attributes),
        }
