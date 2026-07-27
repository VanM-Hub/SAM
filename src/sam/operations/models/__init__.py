"""
Models for Operations Layer — dipisah dari Narrative Engine.

NarrativeImportance, NarrativeType, Narrative dipindah ke sini
agar PresentationEngine bisa mandiri tanpa dependensi narrative/.
"""

from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum


class NarrativeImportance(str, Enum):
    """Tingkat kepentingan dari perspektif manusia.

    BUKAN Runtime severity. Ini adalah UX concept.
    """
    INFORMATION = "information"
    ATTENTION = "attention"
    ACTION_REQUIRED = "action_required"
    CRITICAL = "critical"


class NarrativeType(str, Enum):
    DAILY_SUMMARY = "daily_summary"
    INCIDENT = "incident"
    RECOVERY = "recovery"
    WARNING = "warning"
    RECOMMENDATION = "recommendation"
    LEARNING = "learning"
    APPROVAL_NEEDED = "approval_needed"
    MISSION_UPDATE = "mission_update"
    HEALTH_UPDATE = "health_update"
    TASK_UPDATE = "task_update"
    DEPLOYMENT = "deployment"
    PROTECTION = "protection"


@dataclass(frozen=True)
class Narrative:
    """Sebuah cerita — immutable."""
    title: str
    summary: str
    details: str = ""
    importance: NarrativeImportance = NarrativeImportance.INFORMATION
    narrative_type: NarrativeType = NarrativeType.HEALTH_UPDATE
    action_required: bool = False
    recommended_action: str = ""
    estimated_impact: str = ""
    estimated_time: str = ""
    confidence: float = 1.0
    related_items: List[str] = field(default_factory=list)
