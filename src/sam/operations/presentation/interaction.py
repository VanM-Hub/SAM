"""Interaction — Command objects for all user-to-SAM interactions.

Every UI action is a frozen dataclass (command object).
No execution logic. Commands are sent to Conversation API.
"""

from __future__ import annotations
from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ApproveMission:
    mission_id: str
    reason: str = ""


@dataclass(frozen=True)
class RejectMission:
    mission_id: str
    reason: str = ""


@dataclass(frozen=True)
class CancelMission:
    mission_id: str
    reason: str = ""


@dataclass(frozen=True)
class ResumeMission:
    mission_id: str
    from_step: Optional[str] = None


@dataclass(frozen=True)
class ExecuteRecommendation:
    recommendation_id: str
    confirm: bool = True


@dataclass(frozen=True)
class SimulateRecommendation:
    recommendation_id: str


@dataclass(frozen=True)
class OpenMission:
    mission_id: str


@dataclass(frozen=True)
class OpenTimeline:
    filter_type: str = ""


@dataclass(frozen=True)
class OpenEvidence:
    evidence_id: str
    source_mission: str = ""


@dataclass(frozen=True)
class RefreshDashboard:
    force: bool = False


@dataclass(frozen=True)
class UserQuery:
    text: str
    context: str = ""

    @property
    def is_empty(self) -> bool:
        return not self.text.strip()
