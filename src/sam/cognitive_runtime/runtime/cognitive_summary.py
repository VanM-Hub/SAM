"""Cognitive Summary — ringkasan kognitif (Sprint 191)."""
from __future__ import annotations
from dataclasses import dataclass

from ..context.cognitive_context import CognitiveContext


@dataclass(frozen=True)
class CognitiveSummary:
    """Ringkasan (immutable)."""
    cognitive_id: str = ""
    entry_count: int = 0
    scope: str = ""


class CognitiveSummarizer:
    """Summarizer kognitif. Deterministis."""

    def summarize(self, context: CognitiveContext) -> CognitiveSummary:
        return CognitiveSummary(
            cognitive_id=context.cognitive_id,
            entry_count=context.entry_count(),
            scope=context.scope,
        )
