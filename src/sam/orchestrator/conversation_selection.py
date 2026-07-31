# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 125 - Runtime Selection: conversation_selection.

Read-only conversation bridge for runtime selection.
"""
from __future__ import annotations

from typing import Dict, Optional, Tuple

from .runtime_selector import RuntimeSelector, RuntimeSelection
from .selection_policy import SelectionPolicy
from .selection_summary import SelectionSummary


class ConversationSelectionBridge:
    """Read-only bridge exposing runtime selection."""

    def __init__(self, selector: RuntimeSelector) -> None:
        self._selector = selector

    def select(self, inventory) -> RuntimeSelection:
        return self._selector.select(inventory)

    def summarize(self, selection: RuntimeSelection) -> SelectionSummary:
        return SelectionSummary(
            policy=self._selector._policy.name,
            chain=selection.chain,
            total_candidates=len(selection.scores),
        )

    def chain_of(self, selection: RuntimeSelection) -> Tuple[str, ...]:
        return selection.chain
