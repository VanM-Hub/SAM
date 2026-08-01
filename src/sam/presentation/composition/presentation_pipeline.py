"""Sprint 276 - Presentation Layer: pipeline (deskriptif, tanpa IO)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class PresentationPipeline:
    """Pipeline desktop sebagai urutan stage deskriptif."""

    stages: Tuple[str, ...] = (
        "foundation",
        "workspace",
        "panels",
        "dashboard",
        "runtime",
        "monitoring",
        "certification",
        "integration",
    )

    @property
    def first(self) -> str:
        return self.stages[0]

    @property
    def last(self) -> str:
        return self.stages[-1]

    def as_dict(self) -> dict:
        return {"stages": list(self.stages)}
