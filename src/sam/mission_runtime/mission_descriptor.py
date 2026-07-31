# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 134 - Mission Foundation: mission_descriptor.

Describes a mission for discovery. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Tuple


@dataclass(frozen=True)
class MissionDescriptor:
    """Immutable description of a mission."""

    mission_id: str
    name: str = ""
    category: str = "mission"
    description: str = ""
    tags: Tuple[str, ...] = field(default_factory=tuple)

    @property
    def is_identifiable(self) -> bool:
        return bool(self.mission_id)
