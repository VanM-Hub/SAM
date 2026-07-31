"""Sprint 262 - Runtime Registry: runtime_summary (ringkasan deterministik)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from .runtime_registry import RuntimeRegistry


@dataclass(frozen=True)
class RuntimeSummary:
    """Ringkasan statis registry runtime (tanpa IO)."""

    registry: RuntimeRegistry

    @property
    def total(self) -> int:
        return len(self.registry)

    def layer_names(self) -> Tuple[str, ...]:
        return tuple(
            r.descriptor.name for r in self.registry.refs
            if r.role in ("layer", "runtime")
        )

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "layers": list(self.layer_names()),
        }
