from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum
from datetime import datetime


class ExplanationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Evidence(BaseModel):
    """Bukti yang mendukung penjelasan."""
    source: str  # telemetry event id, log file, dll.
    description: str
    timestamp: datetime
    confidence: float = 0.8  # 0.0-1.0


class Impact(BaseModel):
    """Dampak dari kejadian."""
    description: str
    severity: ExplanationSeverity
    affected_components: List[str] = Field(default_factory=list)
    affected_tasks: List[str] = Field(default_factory=list)


class Recommendation(BaseModel):
    """Rekomendasi tindakan."""
    description: str
    priority: int = 0  # 0-10
    action: Optional[str] = None  # "restart", "approve", "investigate", dll.
    action_target: Optional[str] = None


class Explanation(BaseModel):
    """Penjelasan lengkap untuk sebuah event/task."""
    id: str
    title: str
    description: str
    severity: ExplanationSeverity
    timestamp: datetime

    # Komponen penjelasan
    why: str  # Mengapa terjadi?
    evidence: List[Evidence] = Field(default_factory=list)
    impact: Optional[Impact] = None
    recommendation: Optional[Recommendation] = None

    # Metadata
    event_id: Optional[str] = None
    task_id: Optional[str] = None
    correlation_id: Optional[str] = None
    confidence: float = 0.9

    class Config:
        frozen = True
