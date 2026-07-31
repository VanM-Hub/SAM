"""Sprint 265 - Intelligence Runtime: runtime_session (sesi pipeline)."""
from __future__ import annotations

from dataclasses import dataclass, field

from .runtime_report import RuntimeReport


@dataclass(frozen=True)
class RuntimeSession:
    """Sesi immutable: catatan hasil satu penjalanan pipeline."""

    report: RuntimeReport = field(default_factory=RuntimeReport)
    completed: bool = False

    def as_dict(self) -> dict:
        return {
            "completed": self.completed,
            "report": self.report.as_dict(),
        }
