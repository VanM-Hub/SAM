"""PolicyCard — shared read-only dashboard primitive for Artifact Runtime."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PolicyCard:
    """Immutable dashboard card (read-only)."""
    key: str
    group: str
    kind: str
    value: str
    label: str = ""
    status: str = "ready"

    @property
    def verdict(self) -> str:
        return self.status
