# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 125 - Runtime Selection: selection_summary.

Summarizes a selection outcome. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass(frozen=True)
class SelectionSummary:
    """Immutable summary of a runtime selection."""

    policy: str
    chain: Tuple[str, ...]
    total_candidates: int = 0

    @property
    def selected_count(self) -> int:
        return len(self.chain)
