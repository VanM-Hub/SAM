"""
Mission Contracts — Phase 0
"""

from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class MissionStatus(str, Enum):
    ACTIVE = "active"
    DEGRADED = "degraded"
    FAILED = "failed"
    COMPLETED = "completed"


class Objective(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    status: MissionStatus = MissionStatus.ACTIVE


class Mission(BaseModel):
    id: str
    name: str
    description: str
    objectives: List[Objective]
    priority: int = 1
    min_health: float = 0.8
