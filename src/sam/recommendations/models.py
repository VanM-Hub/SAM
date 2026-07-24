"""Recommendation Engine models for SAM Framework."""

from enum import Enum
from datetime import datetime
from typing import Dict, Any, Optional
from pydantic import BaseModel, Field
import uuid


class RecommendationSeverity(str, Enum):
    """Severity levels for recommendations."""

    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendationStatus(str, Enum):
    """Status of a recommendation."""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    DISMISSED = "dismissed"
    EXECUTED = "executed"


class Recommendation(BaseModel):
    """A recommendation generated from a pattern detection."""

    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    rule_id: str
    pattern_detection_id: str
    severity: RecommendationSeverity
    title: str
    description: str
    action_hint: str
    status: RecommendationStatus = RecommendationStatus.ACTIVE
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    model_config = {
        "frozen": False,  # Allow status updates
        "str_strip_whitespace": True,
    }