"""Sprint 264 - Context Assembly: context_summary (ringkasan konteks)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict

from .context_snapshot import ContextSnapshot


@dataclass(frozen=True)
class ContextSummary:
    """Ringkasan statis sebuah ContextSnapshot."""

    def summarize(self, snapshot: ContextSnapshot) -> Dict[str, object]:
        return {
            "section_count": len(snapshot.sections),
            "sections": list(snapshot.sections.keys()),
            "payload_size": {
                k: len(v) for k, v in snapshot.sections.items()
            },
        }
