"""Sprint 265 - Intelligence Runtime: runtime_status (status immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict


@dataclass(frozen=True)
class RuntimeStatus:
    """Status runtime (preview-only, deterministic)."""

    state: str = "ready"
    mode: str = "preview"

    def as_dict(self) -> Dict[str, object]:
        return {"state": self.state, "mode": self.mode}
