"""Sprint 265 - Intelligence Runtime: runtime_pipeline.

Pipeline tetap (deterministik): Registry -> Graph -> Context -> Validation
-> Assembly -> Report. Tidak menjalankan runtime eksternal.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class RuntimePipeline:
    """Definisi urutan tahap pipeline Intelligence Runtime."""

    stages: Tuple[str, ...] = (
        "Registry",
        "Graph",
        "Context",
        "Validation",
        "Assembly",
        "Report",
    )

    def index(self, stage: str) -> int:
        return self.stages.index(stage)

    def __len__(self) -> int:
        return len(self.stages)
