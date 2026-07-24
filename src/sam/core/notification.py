from __future__ import annotations

from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum
import uuid


class NotificationSeverity(str, Enum):
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class Notification(BaseModel):
    """Immutable notification."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    type: str
    severity: NotificationSeverity
    title: str
    message: str
    source: str
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {"frozen": True}
