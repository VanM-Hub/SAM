"""Runtime Pipeline — engine pipeline connector runtime.

Sprint 121 — Connector Runtime.
Pipeline tahapan yang bisa dijalankan/diinspeksi (preview-only).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List


@dataclass(frozen=True)
class PipelineStage:
    """Satu tahap pipeline."""
    name: str
    enabled: bool = True
    status: str = "pending"  # pending | ready | not_ready


@dataclass(frozen=True)
class RuntimePipeline:
    """Definisi pipeline runtime."""
    stages: List[PipelineStage] = field(default_factory=list)


class RuntimePipelineBuilder:
    """Bangun pipeline standard connector runtime."""

    STAGE_NAMES = [
        "registry", "discovery", "capability", "binding",
        "session", "routing", "translation", "preview",
    ]

    def build(self) -> RuntimePipeline:
        return RuntimePipeline(stages=[
            PipelineStage(name, enabled=True, status="ready")
            for name in self.STAGE_NAMES
        ])
