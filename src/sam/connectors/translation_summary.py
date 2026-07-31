"""Translation Summary — engine ringkasan terjemahan.

Sprint 118 — Connector Translation.
Ringkasan hasil terjemahan (read-only).
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import List

from .translation_result import TranslationResult


@dataclass(frozen=True)
class TranslationSummary:
    """Ringkasan terjemahan."""
    total: int = 0
    success: int = 0
    failures: int = 0


class TranslationSummarizer:
    """Ringkasan hasil terjemahan."""

    def summarize(self, results: List[TranslationResult]) -> TranslationSummary:
        success = sum(1 for r in results if r.success)
        return TranslationSummary(len(results), success, len(results) - success)
