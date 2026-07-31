# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 133 - Certification: orchestration_manifest.

Manifest of the 11 orchestration subsystems. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class OrchestrationManifest:
    """Immutable manifest of the orchestration runtime."""

    version: str = "12.0.0"
    subsystems: Tuple[str, ...] = field(
        default_factory=lambda: (
            "Orchestration Foundation",
            "Runtime Discovery",
            "Runtime Selection",
            "Pipeline Builder",
            "Dependency Resolver",
            "Scheduling",
            "Coordination",
            "Synchronization",
            "Monitoring",
            "Runtime Engine",
            "Certification",
        )
    )

    @property
    def subsystem_count(self) -> int:
        return len(self.subsystems)
