# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 125 - Runtime Selection: selection_policy.

Policy that ranks runtime candidates. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class SelectionPolicy:
    """Immutable ranking policy for runtime selection."""

    name: str
    weights: Dict[str, float] = field(default_factory=dict)
    preferred_tags: Tuple[str, ...] = field(default_factory=tuple)

    def weight(self, dimension: str) -> float:
        """Weight for a scoring dimension (0.0 when unspecified)."""
        return self.weights.get(dimension, 0.0)
