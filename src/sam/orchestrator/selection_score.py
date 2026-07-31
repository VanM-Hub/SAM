# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 125 - Runtime Selection: selection_score.

Scoring result for a runtime candidate. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class SelectionScore:
    """Immutable score produced during runtime selection."""

    runtime_id: str
    score: float = 0.0
    dimensions: Dict[str, float] = field(default_factory=dict)
