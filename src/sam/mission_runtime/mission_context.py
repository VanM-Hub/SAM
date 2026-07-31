# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 134 - Mission Foundation: mission_context.

Immutable context for a mission. Where a mission lives.
Pure DTO, deterministic, never acts.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, Tuple


@dataclass(frozen=True)
class MissionContext:
    """Immutable snapshot of the environment around a mission."""

    mission_id: str
    source_runtime: str = "unknown"
    tenant: str = "default"
    tags: Tuple[str, ...] = field(default_factory=tuple)
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def is_defined(self) -> bool:
        return bool(self.mission_id)
