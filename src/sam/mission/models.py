"""
Mission Models — Phase 0

Mirrors contracts.mission for internal use with loader/validator.
"""

from pydantic import BaseModel
from typing import List, Optional
from sam.contracts import Mission, MissionStatus, Objective


class MissionModel(BaseModel):
    """Wrapper model used by MissionLoader for YAML parsing."""
    id: str
    name: str
    description: str
    objectives: List[Objective]
    priority: int = 1
    min_health: float = 0.8

    def to_contract(self) -> Mission:
        """Convert to public contract."""
        return Mission(
            id=self.id,
            name=self.name,
            description=self.description,
            objectives=self.objectives,
            priority=self.priority,
            min_health=self.min_health,
        )
