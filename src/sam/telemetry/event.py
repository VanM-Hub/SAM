from pydantic import BaseModel, Field, field_validator
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from uuid import uuid4
import json

from .component import Component
from .event_type import TelemetryEventType


class EventSeverity(str, Enum):
    TRACE = "trace"
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class EventCategory(str, Enum):
    LIFECYCLE = "lifecycle"
    EXECUTION = "execution"
    LEARNING = "learning"
    SAFETY = "safety"
    RECOVERY = "recovery"
    APPROVAL = "approval"
    KNOWLEDGE = "knowledge"
    RESOURCE = "resource"
    COMMUNICATION = "communication"
    OPERATOR = "operator"


class TelemetryEvent(BaseModel):
    """Event resmi SAM — format baku untuk semua telemetry."""

    # Identitas
    id: str = Field(default_factory=lambda: str(uuid4())[:8])
    type: TelemetryEventType
    component: Component

    # Waktu
    timestamp: datetime = Field(default_factory=datetime.utcnow)

    # Severity & Kategori
    severity: EventSeverity = EventSeverity.INFO
    category: EventCategory

    # Pesan manusia
    message: str = Field(..., min_length=1, max_length=500)

    # Metadata teknis
    metadata: Dict[str, Any] = Field(default_factory=dict)

    # Traceability
    correlation_id: Optional[str] = None
    session_id: Optional[str] = None
    workflow_id: Optional[str] = None

    # Durasi (jika relevan)
    duration_ms: Optional[float] = None

    @field_validator('metadata')
    @classmethod
    def validate_metadata(cls, v):
        if v is None:
            return {}
        return v

    def to_json(self) -> str:
        return json.dumps(self.dict(), default=str)

    def to_human(self) -> str:
        """Human-friendly version of the event."""
        return "[{}] {}: {}".format(
            self.timestamp.strftime('%H:%M:%S'),
            self.severity.value.upper(),
            self.message
        )

    model_config = {"frozen": True}
