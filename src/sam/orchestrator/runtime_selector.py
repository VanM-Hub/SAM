# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 125 - Runtime Selection: runtime_selector.

Selects the best runtime chain from the inventory using a policy.
Arranges a chain - never executes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple

from .runtime_inventory import RuntimeInventory
from .selection_policy import SelectionPolicy
from .selection_score import SelectionScore


@dataclass(frozen=True)
class RuntimeSelection:
    """Immutable selection outcome (ordered runtime chain)."""

    chain: Tuple[str, ...] = field(default_factory=tuple)
    scores: Tuple[SelectionScore, ...] = field(default_factory=tuple)

    @property
    def is_selected(self) -> bool:
        return bool(self.chain)


class RuntimeSelector:
    """Selects an ordered runtime chain from an inventory."""

    def __init__(self, policy: SelectionPolicy) -> None:
        self._policy = policy

    def select(self, inventory: RuntimeInventory) -> RuntimeSelection:
        """Return runtimes ordered by pipeline position and policy."""
        ordered = sorted(
            inventory.runtimes,
            key=lambda d: (d.pipeline_position, d.runtime_id),
        )
        scores = tuple(
            SelectionScore(
                runtime_id=d.runtime_id,
                score=self._score(d),
                dimensions={"position": float(d.pipeline_position)},
            )
            for d in ordered
        )
        return RuntimeSelection(
            chain=tuple(s.runtime_id for s in scores),
            scores=scores,
        )

    def _score(self, d) -> float:
        base = self._policy.weight("pipeline") * 1.0
        tag_bonus = 0.0
        for i, t in enumerate(d.tags):
            if t in self._policy.preferred_tags:
                tag_bonus += (i + 1) * self._policy.weight("tag")
        return base + tag_bonus
