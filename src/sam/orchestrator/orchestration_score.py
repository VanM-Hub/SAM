# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 133 - Certification: orchestration_score.

Score for the orchestration runtime. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class OrchestrationScore:
    """Immutable score of orchestration quality."""

    score: float = 100.0
    certified: bool = True

    @property
    def passed(self) -> bool:
        return self.certified and self.score >= 90.0
