"""Sprint 261 - Intelligence Runtime Foundation: contract (kontrak tanpa IO)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class IntelligenceContract:
    """Kontrak aplikasi: preview-only, deterministik, tanpa eksekusi nyata."""

    preview_only: bool = True
    deterministic: bool = True
    synchronous: bool = True
    inference: bool = False
    llm: bool = False
    external_calls: int = 0
    layers: Tuple[str, ...] = (
        "registry",
        "graph",
        "context",
        "validation",
        "assembly",
        "report",
    )

    def as_dict(self) -> dict:
        return {
            "preview_only": self.preview_only,
            "deterministic": self.deterministic,
            "synchronous": self.synchronous,
            "inference": self.inference,
            "llm": self.llm,
            "external_calls": self.external_calls,
            "layers": list(self.layers),
        }
