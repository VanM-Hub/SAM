"""Sprint 275 - Desktop Dashboard: card model (immutable)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class DashboardCard:
    """Model kartu dashboard (deklaratif, read-only)."""

    title: str
    source_runtime: str = ""
    kind: str = "card"
    size: int = 1
    sections: Tuple[str, ...] = ()

    def with_sections(self, *sections: str) -> "DashboardCard":
        return DashboardCard(
            title=self.title,
            source_runtime=self.source_runtime,
            kind=self.kind,
            size=self.size,
            sections=self.sections + tuple(sections),
        )

    def as_dict(self) -> dict:
        return {
            "title": self.title,
            "source_runtime": self.source_runtime,
            "kind": self.kind,
            "size": self.size,
            "sections": list(self.sections),
        }
