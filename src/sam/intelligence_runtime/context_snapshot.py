"""Sprint 264 - Context Assembly: context_snapshot (context immutable)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class ContextSnapshot:
    """Snapshot immutable hasil perakitan konteks runtime."""

    sections: Dict[str, Dict[str, object]] = field(default_factory=dict)
    order: Tuple[str, ...] = ()

    def section(self, name: str) -> Dict[str, object]:
        return self.sections.get(name, {})

    def as_dict(self) -> dict:
        return {
            "sections": {k: dict(v) for k, v in self.sections.items()},
            "order": list(self.order),
        }
