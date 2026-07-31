# Copyright 2026 VanM-Hub. Licensed under Apache-2.0.
"""Sprint 135 - Mission Definition: conversation_definition.

Read-only conversation bridge for mission definition.
"""
from __future__ import annotations

from typing import Dict, Optional

from .mission_definition import MissionDefinition
from .mission_validator import MissionValidator, MissionValidationReport
from .mission_scope import MissionScope
from .mission_constraints import MissionConstraints
from .mission_metadata import MissionMetadata


class ConversationDefinitionBridge:
    """Read-only bridge exposing mission definition."""

    def __init__(self) -> None:
        self._validator = MissionValidator()

    def define(self, mission_id: str) -> MissionDefinition:
        return MissionDefinition(
            mission_id=mission_id,
            scope=MissionScope(),
            constraints=MissionConstraints(preview_only=True),
            metadata=MissionMetadata(mission_id=mission_id),
        )

    def validate(self, definition: MissionDefinition) -> MissionValidationReport:
        return self._validator.validate(definition)

    def summary(self, definition: MissionDefinition) -> Dict[str, str]:
        return {
            "mission_id": definition.mission_id,
            "version": definition.metadata.version,
            "plan_only": str(definition.constraints.is_plan_only),
        }
