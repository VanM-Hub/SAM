"""Sprint 261 - Intelligence Runtime Foundation: capability."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class IntelligenceCapability:
    """Kapabilitas yang dimiliki Intelligence Runtime (preview-only)."""

    assemble_context: bool = True
    validate_runtime: bool = True
    build_graph: bool = True
    certify: bool = True
    monitor: bool = True
    bundle: bool = True
    supported_modes: Tuple[str, ...] = ("registry", "graph", "context", "report")

    def as_dict(self) -> dict:
        return {
            "assemble_context": self.assemble_context,
            "validate_runtime": self.validate_runtime,
            "build_graph": self.build_graph,
            "certify": self.certify,
            "monitor": self.monitor,
            "bundle": self.bundle,
            "supported_modes": list(self.supported_modes),
        }
