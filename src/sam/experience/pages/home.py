from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class HomeStatus(str, Enum):
    HEALTHY = "healthy"
    BUSY = "busy"
    RECOVERING = "recovering"
    LEARNING = "learning"
    STARTING = "starting"
    STOPPING = "stopping"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class HomeSection(str, Enum):
    SYSTEM = "system"
    MISSION = "mission"
    ACTIVITY = "activity"
    ATTENTION = "attention"
    CHANGES = "changes"
    RECOMMENDATIONS = "recommendations"


class HomeModel(BaseModel):
    """Immutable ViewModel untuk halaman Home."""

    # Sistem
    status: HomeStatus = HomeStatus.HEALTHY
    status_message: str = "Everything is healthy"
    system_health: float = 100.0  # 0-100

    # Mission
    mission_name: str = "Protect OpenClaw Runtime"
    mission_health: float = 100.0  # 0-100

    # Aktivitas
    current_activity: str = "Monitoring runtime"
    active_tasks: int = 0
    recent_changes: List[Dict[str, Any]] = Field(default_factory=list)  # max 5

    # Perhatian
    needs_attention: bool = False
    pending_approvals: int = 0
    pending_tasks: int = 0
    recommendations: List[str] = Field(default_factory=list)  # max 3

    # Info tambahan
    uptime: str = "0h 0m"
    last_updated: datetime = Field(default_factory=datetime.utcnow)
    operator_name: Optional[str] = None

    # Metadata
    sections: List[HomeSection] = Field(
        default_factory=lambda: [
            HomeSection.SYSTEM,
            HomeSection.MISSION,
            HomeSection.ACTIVITY,
            HomeSection.ATTENTION,
            HomeSection.CHANGES,
            HomeSection.RECOMMENDATIONS,
        ]
    )

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dict for serialization."""
        return self.model_dump()

    class Config:
        frozen = True
