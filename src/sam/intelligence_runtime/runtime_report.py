"""Sprint 265 - Intelligence Runtime: runtime_report (laporan hasil jalur pipeline)."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, Tuple


@dataclass(frozen=True)
class RuntimeReport:
    """Laporan immutable hasil penjalanan pipeline Intelligence Runtime."""

    stages: Tuple[str, ...] = ()
    artifacts: Dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "stages": list(self.stages),
            "artifacts": dict(self.artifacts),
        }
