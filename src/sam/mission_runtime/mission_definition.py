# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 135 - Mission Definition: mission_definition.

Full definition of a mission. Pure DTO, immutable.
"""
from __future__ import annotations

from dataclasses import dataclass

from .mission_scope import MissionScope
from .mission_constraints import MissionConstraints
from .mission_metadata import MissionMetadata


@dataclass(frozen=True)
class MissionDefinition:
    """Immutable complete definition of a mission."""

    mission_id: str
    scope: MissionScope
    constraints: MissionConstraints
    metadata: MissionMetadata

    @property
    def is_well_defined(self) -> bool:
        return bool(self.mission_id) and bool(self.metadata.version)
