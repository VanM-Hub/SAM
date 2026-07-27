from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ActivityType(str, Enum):
    """Jenis aktivitas manusia."""
    TASK = "task"
    SYSTEM = "system"
    KNOWLEDGE = "knowledge"
    MEMORY = "memory"
    PLUGIN = "plugin"
    MISSION = "mission"
    GUARDIAN = "guardian"
    USER = "user"


class ActivitySeverity(str, Enum):
    """Tingkat keparahan aktivitas (manusia)."""
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ActivityItem(BaseModel):
    """Satu item dalam timeline."""
    id: str
    type: ActivityType
    severity: ActivitySeverity
    title: str                      # "Repair task started"
    description: Optional[str] = None  # Detail tambahan
    timestamp: datetime
    duration_ms: Optional[float] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TimelineFilter(BaseModel):
    """Filter untuk timeline."""
    types: List[ActivityType] = Field(default_factory=list)
    severities: List[ActivitySeverity] = Field(default_factory=list)
    query: Optional[str] = None
    from_time: Optional[datetime] = None
    to_time: Optional[datetime] = None
    limit: int = 100


class TimelineModel(BaseModel):
    """ViewModel untuk halaman Timeline."""
    activities: List[ActivityItem]
    total: int
    filtered: int
    filters: TimelineFilter
    last_updated: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        frozen = True
