"""Sprint 264 - Context Assembly: context_report (laporan konteks)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .context_snapshot import ContextSnapshot


@dataclass(frozen=True)
class ContextReport:
    """Laporan statis untuk snapshot konteks."""

    def build(self, snapshot: ContextSnapshot) -> Dict[str, object]:
        return {
            "context": snapshot.as_dict(),
            "summary": {
                "count": len(snapshot.sections),
                "names": list(snapshot.sections.keys()),
            },
        }
